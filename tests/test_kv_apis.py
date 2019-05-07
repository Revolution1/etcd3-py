import json
import pytest
import six

from etcd3.client import Client
from etcd3.models import RangeRequestSortOrder
from etcd3.models import RangeRequestSortTarget
from tests.docker_cli import docker_run_etcd_main
from .envs import protocol, host
from .etcd_go_cli import NO_ETCD_SERVICE
from .etcd_go_cli import etcdctl


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    _, p, _ = docker_run_etcd_main()
    c = Client(host, p, protocol)
    yield c
    c.close()


def clear():
    etcdctl('del', '--from-key', '')


def test_range(client, request):
    clear()
    request.addfinalizer(clear)

    # test get
    etcdctl('put /foo1 v2')
    assert client.range('/foo1').kvs[0].value == b'v2'
    etcdctl('put /foo2 v1')
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
    etcdctl('put some_key_else v')
    r = client.range(all=True)
    assert len(r.kvs) >= 3

    # test limit
    r = client.range(all=True, limit=2)
    assert len(r.kvs) == 2


def test_range_count(client, request):
    clear()
    request.addfinalizer(clear)
    r = client.range('some_key_not_exists', prefix=True, count_only=True)
    assert r.count == 0


def test_put(client, request):
    clear()
    request.addfinalizer(clear)
    client.put('foo', 'bar')
    assert client.range('foo').kvs[0].value == b'bar'
    client.put('foo', 'bra')
    assert client.range('foo').kvs[0].value == b'bra'


def test_delete(client, request):
    clear()
    request.addfinalizer(clear)
    client.put('foo', 'bar')
    client.put('fop', 'bar')
    assert len(client.range('fo', prefix=True).kvs) == 2
    client.delete_range('fo', prefix=True)
    assert not client.range('fo', prefix=True).kvs


def test_compact(client, request):
    out = etcdctl('put some thing', json=True)
    if six.PY3:  # pragma: no cover
        out = six.text_type(out, encoding='utf-8')
    rev = json.loads(out)['header']['revision']
    assert client.compact(rev, physical=False)


def test_txn(client, request):
    clear()
    request.addfinalizer(clear)
    etcdctl('put flag ok')
    etcdctl('put foo bar')
    etcdctl('put fizz buzz')

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

    etcdctl('put flag ok')
    etcdctl('put foo bar')
    etcdctl('put fizz buzz')

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
