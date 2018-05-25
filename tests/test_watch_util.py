import time

import pytest
import socket

from etcd3 import Client, EventType
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
def test_watcher(client):
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

    with pytest.raises(RuntimeError):
        w.runDaemon()
    with pytest.raises(RuntimeError):
        w.run()

    assert w.watching
    assert w._thread.is_alive

    etcdctl('put foo bar')
    etcdctl('put foo bar')
    etcdctl('del foo')
    etcdctl('put fizz buzz')
    etcdctl('put fizz buzz')
    etcdctl('put fizz buzz')

    time.sleep(1)
    w.stop()

    assert not w.watching
    assert not w._thread.is_alive()

    assert len(foo_list) == 3
    assert len(fizz_list) == 3
    assert len(del_list) == 1
    assert len(put_list) == 5
    assert len(all_list) == 6

    etcdctl('put foo bar')
    etcdctl('put fizz buzz')

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
        etcdctl('put foo bar')
        for e in w:
            if not times:
                break
            assert e.key == b'foo'
            assert e.value == b'bar'
            etcdctl('put foo bar')
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
