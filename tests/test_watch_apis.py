import pytest

from etcd3.client import Client
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


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_watch_api(client, request):
    clear()
    request.addfinalizer(clear)

    times = 5
    created = False
    with client.watch_create(key='test_key', progress_notify=True) as r:
        for i in r:
            if not times:  # pragma: no cover
                break
            if not created:
                created = i.created
                assert created
            etcdctl('put test_key test_value')
            if i.events:
                assert i.events[0].kv.key == b'test_key'
                assert i.events[0].kv.value == b'test_value'
                times -= 1

    times = 5
    created = False
    with client.watch_create(all=True, prev_kv=True) as r:
        for i in r:
            if not times:  # pragma: no cover
                break
            if not created:
                created = i.created
                assert created
            etcdctl('put test_key test_value')
            if i.events:
                assert i.events[0].kv.key == b'test_key'
                assert i.events[0].kv.value == b'test_value'
                times -= 1

    times = 5
    created = False
    with client.watch_create('test', prefix=True) as r:
        for i in r:
            if not times:  # pragma: no cover
                break
            if not created:
                created = i.created
                assert created
            etcdctl('put test_key test_value')
            if i.events:
                assert i.events[0].kv.key == b'test_key'
                assert i.events[0].kv.value == b'test_value'
                times -= 1
    # there is no way to test cancel request, cause we cannot get the watcher id
    # but it may be supported in the future
    # client.watch_cancel(123123)
