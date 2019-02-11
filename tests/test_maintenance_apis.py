import json
import pytest
import six

from etcd3 import Client
from etcd3.models import etcdserverpbAlarmType
from tests.docker_cli import docker_run_etcd_main
from .envs import protocol, host
from .etcd_go_cli import NO_ETCD_SERVICE, etcdctl


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    _, p, _ = docker_run_etcd_main()
    c = Client(host, p, protocol)
    yield c
    c.close()


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_hash(client):
    assert client.hash().hash


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_status(client):
    assert client.status().version


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_defragment(client):
    assert client.defragment()


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_alarm(client):
    assert client.alarm_activate(0, etcdserverpbAlarmType.NOSPACE)
    assert client.alarm_get(0, etcdserverpbAlarmType.NOSPACE)
    assert client.alarm_deactivate(0, etcdserverpbAlarmType.NOSPACE)


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_snapshot(client):
    out = etcdctl('put some thing', json=True)
    if six.PY3:  # pragma: no cover
        out = six.text_type(out, encoding='utf-8')
    rev = json.loads(out)['header']['revision']
    etcdctl('compaction --physical %s' % (rev - 10), raise_error=False)
    etcdctl('defrag')

    r = client.snapshot()
    with open('/tmp/etcd-snap.db', 'wb') as f:
        for i in r:
            assert i.blob
            f.write(i.blob)
    assert etcdctl('snapshot status /tmp/etcd-snap.db')
