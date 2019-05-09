import time
from threading import Thread

import pytest

from etcd3.client import Client
from tests.docker_cli import docker_run_etcd_main
from .envs import protocol, host
from .etcd_go_cli import NO_ETCD_SERVICE, etcdctl


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    _, p, _ = docker_run_etcd_main()
    c = Client(host, p, protocol)
    yield c
    c.close()


class context:
    def __init__(self):
        self.exit = False


def clear():
    etcdctl('del', '--from-key', '')


KEY = 'test-lock'


@pytest.mark.timeout(60)
def test_lock_flow(client):
    clear()
    holds = {}

    def hold(name, ctx):
        lock = None
        try:
            lock = holds[name] = client.lock(KEY)
            print("%s is holding the lock" % name)
            while not ctx.exit:
                time.sleep(0.5)
        finally:
            if lock:
                client.unlock(lock.key)
                holds[name] = None

    ctx1 = context()
    ctx2 = context()

    t1 = Thread(target=lambda: hold('User1', ctx1))
    t2 = Thread(target=lambda: hold('User2', ctx2))
    t1.setDaemon(True)
    t2.setDaemon(True)
    t1.start()

    time.sleep(1)
    assert holds['User1'].key
    key1 = holds['User1'].key
    keys1 = client.range(key1)
    assert keys1.kvs[0].lease
    assert client.lease_time_to_live(keys1.kvs[0].lease).TTL > 0
    assert 'User2' not in holds

    t2.start()
    time.sleep(1)
    assert holds['User1'].key
    key1 = holds['User1'].key
    keys1 = client.range(key1)
    assert keys1.kvs[0].lease
    assert client.lease_time_to_live(keys1.kvs[0].lease).TTL > 0
    assert 'User2' not in holds

    print("killing lock1")
    ctx1.exit = True
    t1.join()
    time.sleep(1)
    assert holds['User1'] is None
    # https://github.com/etcd-io/etcd/blob/3546c4868cec93e1587471b42fd815684a7dd439/clientv3/concurrency/mutex.go#L82
    # only key been deleted not the lease
    assert client.range(key1).kvs is None
    assert holds['User2'].key
    key2 = holds['User2'].key
    keys2 = client.range(key2)
    assert keys2.kvs[0].lease
    assert client.lease_time_to_live(keys2.kvs[0].lease).TTL > 0

    ctx2.exit = True
    t2.join()
    assert holds['User1'] is None
    assert holds['User2'] is None
    assert client.range(key2).kvs is None

    # with lease
    lease1 = client.Lease(5)
    lease1.grant()
    lock1 = client.lock('test_lock', lease1.ID)
    assert lock1.key.startswith(b'test_lock/')

    lease2 = client.Lease(15)
    lease2.grant()
    start_lock_ts = time.time()
    client.lock('test_lock', lease2.ID)
    assert (time.time() - start_lock_ts) > 3

    lease2.revoke()

    lease3 = client.Lease(5)
    lease3.grant()
    start_lock_ts = time.time()
    lock3 = client.lock('test_lock', lease3.ID)
    assert (time.time() - start_lock_ts) < 2

    client.unlock(lock3.key)
