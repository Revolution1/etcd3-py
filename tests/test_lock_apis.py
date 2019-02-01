import time

import pytest

from etcd3.client import Client
from tests.docker_cli import docker_run_etcd_main
from .envs import protocol, host, port
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


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_hash(client):
    assert client.hash().hash


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_lock_flow(client):
    lease1 = client.Lease(5)
    lease1.grant()
    lock1 = client.lock('test_lock', lease1._ID)
    assert lock1.key.startswith(b'test_lock/')

    lease2 = client.Lease(15)
    lease2.grant()
    start_lock_ts = time.time()
    client.lock('test_lock', lease2._ID)
    assert (time.time() - start_lock_ts) > 3

    lease2.revoke()

    lease3 = client.Lease(5)
    lease3.grant()
    start_lock_ts = time.time()
    lock3 = client.lock('test_lock', lease3._ID)
    assert (time.time() - start_lock_ts) < 2

    client.unlock(lock3.key)
