import logging
import time
from threading import Thread

import pytest

from etcd3 import Client, Lock
from .envs import protocol, host, port
from .etcd_go_cli import NO_ETCD_SERVICE, etcdctl

logging.getLogger().setLevel(logging.DEBUG)


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    c = Client(host, port, protocol)
    yield c
    c.close()


class context:
    def __init__(self):
        self.exit = False


def clear():
    etcdctl('del', '--from-key', '')


@pytest.mark.timeout(60)
def test_lock(client):
    clear()
    holds = {}

    def hold(lock, name, ctx):
        with lock:
            holds[name] = name
            print("%s is holding the lock" % name)
            lock.acquire()
            while not ctx.exit:
                time.sleep(0.5)
        holds[name] = None

    l1 = client.Lock('lock-test', lock_ttl=2)
    l2 = client.Lock('lock-test', lock_ttl=2)

    ctx1 = context()
    ctx2 = context()

    t1 = Thread(target=lambda: hold(l1, 'User1', ctx1))
    t2 = Thread(target=lambda: hold(l2, 'User2', ctx2))
    t1.setDaemon(True)
    t2.setDaemon(True)
    t1.start()

    time.sleep(1)
    assert holds['User1'] == 'User1'
    assert l1.holders() == 1
    assert l2.holders() == 1

    t2.start()
    time.sleep(1)
    assert l1.is_acquired
    assert not l2.is_acquired
    assert holds['User1'] == 'User1'
    assert 'User2' not in holds
    assert l1.holders() == 1
    assert l2.holders() == 1

    print("killing lock1")
    ctx1.exit = True
    t1.join()
    time.sleep(1)
    assert not l1.is_acquired
    assert l2.is_acquired
    assert holds['User1'] is None
    assert holds['User2'] == 'User2'
    assert l1.holders() == 1
    assert l2.holders() == 1

    ctx2.exit = True
    t2.join()
    assert holds['User1'] is None
    assert holds['User2'] is None
    assert l1.holders() == 0
    assert l2.holders() == 0


@pytest.mark.timeout(60)
def test_reentrant_lock_host(client):
    clear()
    holds = {}

    def hold(lock, name, ctx):
        with lock:
            holds[name] = name
            print("%s is holding the lock" % name)
            lock.acquire()
            while not ctx.exit:
                time.sleep(0.5)
        holds[name] = None

    l1 = client.Lock('lock-test', lock_ttl=2, reentrant=Lock.HOST)
    l2 = client.Lock('lock-test', lock_ttl=2, reentrant=Lock.HOST)

    ctx1 = context()
    ctx2 = context()

    t1 = Thread(target=lambda: hold(l1, 'User1', ctx1))
    t2 = Thread(target=lambda: hold(l2, 'User2', ctx2))
    t1.setDaemon(True)
    t2.setDaemon(True)
    t1.start()

    time.sleep(2)
    assert holds['User1'] == 'User1'
    assert l1.holders() == 1
    assert l2.holders() == 1

    t2.start()
    time.sleep(1)
    assert l1.is_acquired
    assert l2.is_acquired
    assert holds['User1'] == 'User1'
    assert holds['User2'] == 'User2'
    assert l1.holders() == 2
    assert l2.holders() == 2

    print("killing lock1")
    ctx1.exit = True
    t1.join()
    time.sleep(1)
    assert not l1.is_acquired
    assert l2.is_acquired
    assert holds['User1'] == None
    assert holds['User2'] == 'User2'
    assert l1.holders() == 1
    assert l2.holders() == 1

    ctx2.exit = True
    t2.join()
    assert holds['User1'] is None
    assert holds['User2'] is None
    assert l1.holders() == 0
    assert l2.holders() == 0


@pytest.mark.timeout(60)
def test_reentrant_lock(client):
    clear()
    holds = {}

    def hold(lock, name, ctx):
        with lock:
            holds[name] = name
            print("%s is holding the lock" % name)
            lock.acquire()
            while not ctx.exit:
                time.sleep(0.5)
        holds[name] = None

    l1 = client.Lock('lock-test', lock_ttl=2, reentrant=Lock.PROCESS)
    l2 = client.Lock('lock-test', lock_ttl=2, reentrant=Lock.PROCESS)

    ctx1 = context()
    ctx2 = context()

    t1 = Thread(target=lambda: hold(l1, 'User1', ctx1))
    t2 = Thread(target=lambda: hold(l2, 'User2', ctx2))
    t1.setDaemon(True)
    t2.setDaemon(True)
    t1.start()

    time.sleep(2)
    assert holds['User1'] == 'User1'
    assert l1.holders() == 1
    assert l2.holders() == 1

    t2.start()
    time.sleep(1)
    assert l1.is_acquired
    assert l2.is_acquired
    assert holds['User1'] == 'User1'
    assert holds['User2'] == 'User2'
    assert l1.holders() == 2
    assert l2.holders() == 2

    print("killing lock1")
    ctx1.exit = True
    t1.join()
    time.sleep(1)
    assert not l1.is_acquired
    assert l2.is_acquired
    assert holds['User1'] == None
    assert holds['User2'] == 'User2'
    assert l1.holders() == 1
    assert l2.holders() == 1

    ctx2.exit = True
    t2.join()
    assert holds['User1'] is None
    assert holds['User2'] is None
    assert l1.holders() == 0
    assert l2.holders() == 0
