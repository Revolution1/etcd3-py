import random

import pytest

from etcd3 import Client
from tests.docker_cli import docker_run_etcd_main
from .envs import protocol, host
from .etcd_go_cli import etcdctl, NO_ETCD_SERVICE


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    _, p, _ = docker_run_etcd_main()
    c = Client(host, p, protocol)
    yield c
    c.close()


@pytest.mark.timeout(60)
@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_transaction(client):
    etcdctl('put foo bar')
    txn = client.Txn()
    txn.compare(txn.key('foo').value == 'bar')
    txn.success(txn.put('foo', 'bra'))
    r = txn.commit()
    assert r.succeeded
    assert client.range('foo').kvs[0].value == b'bra'

    txn = client.Txn()
    txn.If(txn.key('foo').value == 'bar')
    txn.Then(txn.put('foo', 'bra'))
    txn.Else(txn.put('foo', 'bar'))
    txn.commit()
    assert client.range('foo').kvs[0].value == b'bar'

    etcdctl('put foo 2')
    txn = client.Txn()
    txn.If(txn.key('foo').value > b'1')
    txn.If(txn.key('foo').value < b'3')
    txn.If(txn.key('foo').value != b'0')
    txn.Then(txn.put('foo', 'bra'))
    r = txn.commit()
    assert r.succeeded
    assert client.range('foo').kvs[0].value == b'bra'

    etcdctl('put foo bar')
    etcdctl('put fizz buzz')
    txn = client.Txn()
    txn.success(txn.range('foo'))
    txn.success(txn.delete('fizz'))
    r = txn.commit()
    assert r.succeeded
    for i in r.responses:
        if 'response_range' in i:
            assert i.response_range.kvs[0].value == b'bar'
        else:  # delete
            assert i.response_delete_range.deleted == 1
    assert not client.range('fizz').kvs

    # no gt and lt
    with pytest.raises(NotImplementedError):
        txn.If(txn.key('foo').value >= b'1')
    with pytest.raises(NotImplementedError):
        txn.If(txn.key('foo').value <= b'1')

    # type should match with target
    with pytest.raises(TypeError):
        txn.If(txn.key('foo').value < 1)
    with pytest.raises(TypeError):
        txn.If(txn.key('foo').version < 'a')
    with pytest.raises(TypeError):
        txn.If(txn.key('foo').create < 'a')
    with pytest.raises(TypeError):
        txn.If(txn.key('foo').mod < 'a')

    with pytest.raises(TypeError):
        txn.If(txn.key('foo').mod.value < 1)

    with pytest.raises(TypeError):
        client.Txn().key(123)

    # range_end
    etcdctl('del', '--from-key', '')
    etcdctl('put foo 1')
    etcdctl('put bar 2')
    etcdctl('put fiz 3')
    etcdctl('put buz 4')

    txn = client.Txn()
    r = txn.compare(txn.key(all=True).value > b'0').commit()
    assert r.succeeded

    txn = client.Txn()
    r = txn.compare(txn.key(all=True).value < b'3').commit()
    assert not r.succeeded

    # target lease
    ID = random.randint(10000, 100000)
    TTL = 60
    r = client.lease_grant(TTL, ID=ID)
    assert r.ID == ID

    hexid = hex(ID)[2:]
    etcdctl('put --lease=%s foo bar' % hexid)

    txn = client.Txn()
    r = txn.compare(txn.key('foo').lease == ID).commit()
    assert r.succeeded
