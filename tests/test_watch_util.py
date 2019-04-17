import socket
import time

import pytest

from etcd3 import Client, EventType
from etcd3.errors import Etcd3WatchCanceled
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


MAX_RETRIES = 3


@pytest.mark.timeout(60)
@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_watcher(client):
    w = client.Watcher(all=True, progress_notify=True, prev_kv=True, max_retries=MAX_RETRIES)
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
    assert w._thread.is_alive()

    with pytest.raises(RuntimeError):  # ensure not running
        w.runDaemon()
    w.watching = False
    try:  # ensure not running
        w.runDaemon()
    except Exception as e:
        assert isinstance(e, RuntimeError)
        assert "watch thread seems running" in str(e)
    w.watching = True
    with pytest.raises(RuntimeError):  # ensure not running
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
        etcdctl('put foo barr')
        revision = None
        for e in w:
            if not times:
                break
            assert e.key == b'foo'
            assert e.value == b'barr'
            if revision:
                assert e.header.revision == revision + 1
            revision = e.header.revision
            etcdctl('put foo barr')
            times -= 1
    assert not w.watching
    assert w._resp.raw.closed

    # test ensure callbacks
    with pytest.raises(TypeError):
        w.clear_callbacks()
        w.runDaemon()


@pytest.mark.timeout(60)
def test_watcher_retry(client):
    w = client.Watcher(all=True, progress_notify=True, prev_kv=True, max_retries=MAX_RETRIES)
    w.onEvent(lambda e: None)
    w.runDaemon()
    times = MAX_RETRIES + 1
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
    assert len(w.errors) == MAX_RETRIES


@pytest.mark.timeout(60)
def test_watcher_watch_once_and_cancel_handling(client):
    # watch once
    old_revision = client.hash().header.revision
    for i in range(10):
        etcdctl('put foo %s' % i)
    w = client.Watcher(all=True, start_revision=old_revision + 1)
    assert w.watch_once().value == b'0'
    assert w.revision == old_revision + 10

    # test watch cancel handling
    compact_revision = client.hash().header.revision
    etcdctl("compaction --physical %s" % compact_revision)
    with pytest.raises(Etcd3WatchCanceled):
        w = client.Watcher(all=True, start_revision=compact_revision - 1)
        w.watch_once()

    with pytest.raises(Etcd3WatchCanceled):
        w = client.Watcher(all=True, start_revision=compact_revision - 1)
        with w:
            for _ in w:
                pass


@pytest.mark.timeout(60)
def test_watcher_rewatch_on_compaction(client):
    # compaction while re-watching
    w = client.Watcher("foo")
    assert w.revision is None
    assert w.start_revision is None
    times = 3
    with w:
        etcdctl('put foo bare')
        revision = None
        for e in w:
            assert w.revision
            assert w.start_revision
            if not times:
                break
            if revision:
                assert e.header.revision == revision + 11
            assert e.key == b'foo'
            assert e.value == b'bare'
            revision = e.header.revision
            for i in range(10):  # these event will be compacted
                etcdctl('put foo %s' % i)
            etcdctl('put foo bare')  # will receive this event when re-watch
            client.compact(client.hash().header.revision, True)
            assert client.hash().header.revision == revision + 11
            # etcdctl("compaction --physical %s" % client.hash().header.revision)
            times -= 1
            w._kill_response_stream()  # trigger a re-watch
