import pytest

from .envs import NO_DOCKER_SERVICE


@pytest.mark.timeout(60)
@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_transaction(client, etcd_cluster):
    etcd_cluster.etcdctl('put foo bar')
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

    etcd_cluster.etcdctl('put foo 2')
    txn = client.Txn()
    txn.If(txn.key('foo').value > b'1')
    txn.If(txn.key('foo').value < b'3')
    txn.If(txn.key('foo').value != b'0')
    txn.Then(txn.put('foo', 'bra'))
    r = txn.commit()
    assert r.succeeded
    assert client.range('foo').kvs[0].value == b'bra'

    etcd_cluster.etcdctl('put foo bar')
    etcd_cluster.etcdctl('put fizz buzz')
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

    with pytest.raises(NotImplementedError):
        txn.If(txn.key('foo').value >= b'1')
    with pytest.raises(NotImplementedError):
        txn.If(txn.key('foo').value <= b'1')
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
