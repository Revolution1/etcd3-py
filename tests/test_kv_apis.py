import json
import pytest
import six

from etcd3.models import RangeRequestSortOrder
from etcd3.models import RangeRequestSortTarget
from .envs import NO_DOCKER_SERVICE


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_range(client, etcd_cluster, clear, request):
    clear()
    request.addfinalizer(clear)

    # test get
    etcd_cluster.etcdctl('put /foo1 v2')
    assert client.range('/foo1').kvs[0].value == b'v2'
    etcd_cluster.etcdctl('put /foo2 v1')
    assert client.range('/foo2').kvs[0].value == b'v1'

    # test prefix and sort
    r = client.range('/foo', prefix=True,
                     sort_order=RangeRequestSortOrder.DESCEND,
                     sort_target=RangeRequestSortTarget.KEY)
    assert r.kvs[0].key == b'/foo2'
    assert r.kvs[1].key == b'/foo1'
    r = client.range('/foo', prefix=True,
                     sort_order=RangeRequestSortOrder.DESCEND,
                     sort_target=RangeRequestSortTarget.VALUE)
    assert r.kvs[0].key == b'/foo1'
    assert r.kvs[1].key == b'/foo2'

    # test all
    etcd_cluster.etcdctl('put some_key_else v')
    r = client.range(all=True)
    assert len(r.kvs) >= 3

    # test limit
    r = client.range(all=True, limit=2)
    assert len(r.kvs) == 2


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_put(client, clear, request):
    clear()
    request.addfinalizer(clear)
    client.put('foo', 'bar')
    assert client.range('foo').kvs[0].value == b'bar'
    client.put('foo', 'bra')
    assert client.range('foo').kvs[0].value == b'bra'


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_delete(client, clear, request):
    clear()
    request.addfinalizer(clear)
    client.put('foo', 'bar')
    client.put('fop', 'bar')
    assert len(client.range('fo', prefix=True).kvs) == 2
    client.delete_range('fo', prefix=True)
    assert not client.range('fo', prefix=True).kvs


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_compact(client, etcd_cluster, request):
    out = etcd_cluster.etcdctl('-w json put some thing')
    if six.PY3:  # pragma: no cover
        out = six.text_type(out, encoding='utf-8')
    rev = json.loads(out)['header']['revision']
    assert client.compact(rev, physical=False)


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_txn(client, etcd_cluster, clear, request):
    clear()
    request.addfinalizer(clear)
    etcd_cluster.etcdctl('put flag ok')
    etcd_cluster.etcdctl('put foo bar')
    etcd_cluster.etcdctl('put fizz buzz')

    compare = [{
        "result": "EQUAL",
        "target": "VALUE",
        "key": "flag",
        "value": "ok"
    }]

    success = [
        client.delete_range('fizz', txn_obj=True),
        client.put('foo', 'bra', txn_obj=True)
    ]

    fail = [
        client.put('fail', 'fff', txn_obj=True)
    ]

    r = client.txn(compare, success, fail)
    assert r.succeeded == True
    assert not client.range('fizz').kvs
    assert client.range('foo').kvs[0].value == b'bra'

    etcd_cluster.etcdctl('put flag ok')
    etcd_cluster.etcdctl('put foo bar')
    etcd_cluster.etcdctl('put fizz buzz')

    compare = [{
        "result": "EQUAL",
        "target": "VALUE",
        "key": "flag",
        "value": "not ok"
    }]
    r = client.txn(compare, success, fail)
    assert 'succeeded' not in r
    assert client.range('foo').kvs[0].value == b'bar'
    assert client.range('fizz').kvs[0].value == b'buzz'
    assert client.range('fail').kvs[0].value == b'fff'
