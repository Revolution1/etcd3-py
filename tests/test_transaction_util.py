import pytest

from etcd3 import Client
from etcd3 import Txn
from .envs import protocol, host, port
from .etcd_go_cli import etcdctl, NO_ETCD_SERVICE


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    c = Client(host, port, protocol)
    yield c
    c.close()


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_transaction(client):
    etcdctl('put foo bar')
    txn = Txn(client)
    txn.compare(txn.key('foo').value == 'bar')
    txn.success(txn.put('foo', 'bra'))
    r = txn.commit()
    assert r.succeeded
    assert client.range('foo').kvs[0].value == b'bra'

    txn = Txn(client)
    txn.If(txn.key('foo').value == 'bar')
    txn.Then(txn.put('foo', 'bra'))
    txn.Else(txn.put('foo', 'bar'))
    txn.commit()
    assert client.range('foo').kvs[0].value == b'bar'

    etcdctl('put foo 2')
    txn = Txn(client)
    txn.If(txn.key('foo').value > b'1')
    txn.If(txn.key('foo').value < b'3')
    txn.If(txn.key('foo').value != b'0')
    txn.Then(txn.put('foo', 'bra'))
    r = txn.commit()
    assert r.succeeded
    assert client.range('foo').kvs[0].value == b'bra'

    etcdctl('put foo bar')
    etcdctl('put fizz buzz')
    txn = Txn(client)
    txn.success(txn.range('foo'))
    txn.success(txn.delete('fizz'))
    r = txn.commit()
    assert r.succeeded
    for i in r.responses:
        if 'response_range' in i:
            assert i.response_range.kvs[0].value == b'bar'
        else:  # delete
            assert i.response_delete_range.deleted == 1
    assert 'kvs' not in client.range('fizz')
