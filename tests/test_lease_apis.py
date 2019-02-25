import random
import time
import pytest
from .envs import NO_DOCKER_SERVICE


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_hash(client):
    assert client.hash().hash


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_lease_flow(client, etcd_cluster):
    ID = random.randint(10000, 100000)
    TTL = 60
    r = client.lease_grant(TTL, ID=ID)
    assert r.ID == ID

    hexid = hex(ID)[2:]
    etcd_cluster.etcdctl('put --lease=%s foo bar' % hexid)
    etcd_cluster.etcdctl('put --lease=%s fizz buzz' % hexid)
    time.sleep(1)
    r = client.lease_time_to_live(ID, keys=True)
    assert r.ID == ID
    assert r.grantedTTL == TTL
    assert r.TTL < TTL
    assert set(r.keys) == {b'foo', b'fizz'}

    for i in client.lease_keep_alive(b'{"ID":%d}\n' % ID):
        assert i.ID == ID
        assert i.TTL == TTL
    r = client.lease_keep_alive_once(ID)
    assert r.ID == ID
    assert r.TTL == TTL
    assert client.lease_revoke(ID)
    assert client.lease_time_to_live(ID).TTL == -1
