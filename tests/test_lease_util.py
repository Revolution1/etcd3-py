import time

import mock
import pytest
import random

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


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_lease_util(client):
    ID = random.randint(10000, 100000)
    TTL = 2  # min is 2sec
    lease = client.Lease(ttl=TTL, ID=ID)
    with lease:
        hexid = hex(ID)[2:]
        etcdctl('put --lease=%s foo bar' % hexid)
        etcdctl('put --lease=%s fizz buzz' % hexid)
        time.sleep(TTL)
        r = lease.time_to_live(keys=True)
        assert r.ID == ID
        assert r.grantedTTL == TTL
        assert r.TTL <= TTL
        assert set(r.keys) == {b'foo', b'fizz'}
        # time.sleep(100)
        assert lease.keeping
        assert lease.alive()
        assert not lease.jammed()
        assert lease._thread.is_alive()

    assert not lease.alive()
    assert not lease.keeping
    assert not lease._thread.is_alive()

    ID = random.randint(10000, 100000)
    TTL = 5  # min is 2sec
    keep_cb = mock.Mock()
    cancel_cb = mock.Mock()

    lease = client.Lease(ttl=TTL, ID=ID)
    lease.grant()
    lease.keepalive(keep_cb=keep_cb, cancel_cb=cancel_cb)
    lease.cancel_keepalive()
    assert keep_cb.called
    assert cancel_cb.called

    lease.keepalive_once()
    lease = client.Lease(ttl=TTL, ID=ID, new=False)
    lease.grant()
    assert lease.alive()
    lease.revoke()

    lease = client.Lease(ttl=TTL)
    lease.grant()
    assert lease.alive()
    lease.revoke()
