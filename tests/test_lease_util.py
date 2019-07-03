import random
import time

import mock
import pytest
import six

from etcd3.client import Client
from tests.docker_cli import docker_run_etcd_main
from .envs import protocol, host
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


def test_lease_util(client):
    ID = random.randint(10000, 100000)
    TTL = 2  # min is 2sec
    lease = client.Lease(ttl=TTL, ID=ID)
    with lease:
        hexid = hex(ID)[2:]
        etcdctl('put --lease=%s foo bar' % hexid)
        etcdctl('put --lease=%s fizz buzz' % hexid)
        time.sleep(TTL)
        r = lease.time_to_live(keys=True)
        assert r.ID == ID
        assert r.grantedTTL == TTL
        assert r.TTL <= TTL
        assert set(r.keys) == {b'foo', b'fizz'}
        # time.sleep(100)
        assert lease.keeping
        assert lease.alive()
        assert not lease.jammed()
        assert lease._thread.is_alive()

    assert not lease.alive()
    assert not lease.keeping
    assert not lease._thread.is_alive()


def test_lease_keep(client):
    ID = random.randint(10000, 100000)
    TTL = 5  # min is 2sec
    keep_cb = mock.Mock()
    cancel_cb = mock.Mock()

    lease = client.Lease(ttl=TTL, ID=ID)
    lease.grant()
    lease.keepalive(keep_cb=keep_cb, cancel_cb=cancel_cb)
    with pytest.raises(RuntimeError):
        lease.keepalive()
    time.sleep(1)
    lease.cancel_keepalive()
    assert keep_cb.called
    assert keep_cb.call_count < 2  # or it keep too fast
    assert cancel_cb.called

    lease.keepalive_once()
    lease = client.Lease(ttl=TTL, ID=ID, new=False)
    lease.grant()
    assert lease.alive()
    lease.revoke()

    lease = client.Lease(ttl=TTL)
    lease.grant()
    assert lease.alive()
    lease.revoke()


def test_release_unlocked_lock(client):
    import threading

    condition = threading.Condition
    if six.PY2:  # pragma: no cover
        condition = threading._Condition

    class Lock(condition):  # pragma: no cover
        def acquire(self, blocking=True, timeout=None):
            print("acquiring lock")
            if six.PY3:
                return super(Lock, self).acquire(blocking, timeout)
            else:
                return super(Lock, self).acquire(blocking)

        def release(self):
            print("releasing lock")
            return super(Lock, self).release()

        def notify_all(self):
            print('notify all')
            return super(Lock, self).notify_all()

        def wait(self, timeout=None):
            print('waiting lock')
            return super(Lock, self).wait(timeout)

        def __enter__(self):
            print("entering lock")
            return super(Lock, self).__enter__()

        def __exit__(self, exc_type, exc_val, exc_tb):
            print("exiting lock")
            return super(Lock, self).__exit__(exc_type, exc_val, exc_tb)

    L = client.Lease(ttl=5)
    L._lock = Lock()
    print("start with lock")
    with L as lease:
        client.put('foo', 'bar', lease=lease.ID)
        client.put('fizz', 'buzz', lease=lease.ID)
        r = lease.time_to_live(keys=True)
        assert set(r.keys) == {b'foo', b'fizz'}
        assert lease.alive()
        print("end with lock")
    assert L._keepalive_error is None
