import time

import pytest
import socket

from etcd3 import EventType
from .envs import NO_DOCKER_SERVICE


@pytest.mark.timeout(60)
@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_watcher(client, etcd_cluster):
    max_retries = 3
    w = client.Watcher(all=True, progress_notify=True, prev_kv=True, max_retries=max_retries)

    foo_list = []
    fizz_list = []
    all_list = []
    del_list = []
    put_list = []
    w.onEvent(lambda e: e.key == b'foo', lambda e: foo_list.append(e))
    w.onEvent('fiz.', lambda e: fizz_list.append(e))
    w.onEvent(EventType.DELETE, lambda e: del_list.append(e))
    w.onEvent(EventType.PUT, lambda e: put_list.append(e))
    w.onEvent(lambda e: all_list.append(e))

    assert len(w.callbacks) == 5

    w.runDaemon()
    time.sleep(0.2)
    live = w._thread.is_alive()

    with pytest.raises(RuntimeError):
        w.runDaemon()
    with pytest.raises(RuntimeError):
        w.run()

    assert w.watching
    assert w._thread.is_alive

    etcd_cluster.etcdctl('put foo bar')
    etcd_cluster.etcdctl('put foo bar')
    etcd_cluster.etcdctl('del foo')
    etcd_cluster.etcdctl('put fizz buzz')
    etcd_cluster.etcdctl('put fizz buzz')
    etcd_cluster.etcdctl('put fizz buzz')

    time.sleep(1)
    w.stop()

    assert not w.watching
    assert not w._thread.is_alive()

    assert len(foo_list) == 3
    assert len(fizz_list) == 3
    assert len(del_list) == 1
    assert len(put_list) == 5
    assert len(all_list) == 6

    etcd_cluster.etcdctl('put foo bar')
    etcd_cluster.etcdctl('put fizz buzz')

    foo_list = []
    fizz_list = []

    w.runDaemon()
    time.sleep(1)
    w.stop()

    assert len(foo_list) == 1
    assert len(fizz_list) == 1
    assert len(all_list) == 8

    w.clear_callbacks()
    assert len(w.callbacks) == 0

    times = 3
    with w:
        etcd_cluster.etcdctl('put foo bar')
        for e in w:
            if not times:
                break
            assert e.key == b'foo'
            assert e.value == b'bar'
            etcd_cluster.etcdctl('put foo bar')
            times -= 1
    assert not w.watching
    assert w._resp.raw.closed

    with pytest.raises(TypeError):  # ensure callbacks
        w.runDaemon()

    # test retry
    w.onEvent(lambda e: None)
    w.runDaemon()
    times = max_retries + 1
    while times:
        time.sleep(0.5)
        if not w._resp.raw.closed:  # directly close the tcp connection
            s = socket.fromfd(w._resp.raw._fp.fileno(), socket.AF_INET, socket.SOCK_STREAM)
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            times -= 1

    assert not w._thread.join()
    assert not w._thread.is_alive()
    assert not w.watching
    assert w._resp.raw.closed
    assert len(w.errors) == max_retries


@pytest.mark.timeout(60)
@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_watcher_cluster(client, etcd_cluster):
    w = client.Watcher(all=True, progress_notify=True, prev_kv=True)
    w.set_default_timeout(2)
    put_list = []
    w.onEvent(EventType.PUT, lambda e: put_list.append(e))

    assert len(w.callbacks) == 1

    w.runDaemon()
    time.sleep(0.2)
    live = w._thread.is_alive()

    with pytest.raises(RuntimeError):
        w.runDaemon()
    with pytest.raises(RuntimeError):
        w.run()

    assert w.watching
    assert w._thread.is_alive

    for i in range(6):
        c = etcd_cluster.containers[i%3]
        etcd_cluster.etcdctl("put key%s val" % i)
        c.kill()
        while not len(put_list) == i+1:
            time.sleep(0.5)
        c.restart()
        etcd_cluster.wait_ready()
        # refresh docker dynamically allocated endpoints
        client.endpoints = etcd_cluster.get_endpoints()
    w.stop()

    assert w._resp.raw.closed
    # ensure all events have been reported
    assert len(put_list) == 6
    # doing a rolling restart twice must generate at least 2 errors
    assert len(w.errors) >= 2
