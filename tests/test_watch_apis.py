import pytest

from .envs import NO_DOCKER_SERVICE


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_watch_api(client, clear, etcd_cluster, request):
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
            etcd_cluster.etcdctl('put test_key test_value')
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
            etcd_cluster.etcdctl('put test_key test_value')
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
            etcd_cluster.etcdctl('put test_key test_value')
            if i.events:
                assert i.events[0].kv.key == b'test_key'
                assert i.events[0].kv.value == b'test_value'
                times -= 1
    # there is no way to test cancel request, cause we cannot get the watcher id
    # but it may be supported in the future
    # client.watch_cancel(123123)
