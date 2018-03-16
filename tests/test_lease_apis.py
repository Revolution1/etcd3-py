import random
import time

import pytest

from etcd3.client import Client
from .envs import protocol, host, port
from .etcd_go_cli import NO_ETCD_SERVICE, etcdctl


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    c = Client(host, port, protocol)
    yield c
    c.close()


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_hash(client):
    assert client.hash().hash


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_lease_flow(client):
    ID = random.randint(10000, 100000)
    TTL = 60
    r = client.lease_grant(TTL, ID=ID)
    assert r.ID == ID

    hexid = hex(ID)[2:]
    etcdctl('put --lease=%s foo bar' % hexid)
    etcdctl('put --lease=%s fizz buzz' % hexid)
    time.sleep(1)
    r = client.lease_time_to_live(ID, keys=True)
    assert r.ID == ID
    assert r.grantedTTL == TTL
    assert r.TTL < TTL
    assert set(r.keys) == {b'foo', b'fizz'}

    for i in client.lease_keep_alive(ID):
        assert i.ID == ID
        assert i.TTL == TTL
    r = client.lease_keep_alive_once(ID)
    assert r.ID == ID
    assert r.TTL == TTL
    assert client.lease_revoke(ID)
    assert client.lease_time_to_live(ID).TTL == -1
