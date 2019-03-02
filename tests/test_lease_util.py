import time

import mock
import pytest
import random

from .envs import NO_DOCKER_SERVICE


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_lease_util(client, etcd_cluster):
    ID = random.randint(10000, 100000)
    TTL = 2  # min is 2sec
    lease = client.Lease(ttl=TTL, ID=ID)
    with lease:
        hexid = hex(ID)[2:]
        etcd_cluster.etcdctl('put --lease=%s foo bar' % hexid)
        etcd_cluster.etcdctl('put --lease=%s fizz buzz' % hexid)
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
    time.sleep(1)
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
