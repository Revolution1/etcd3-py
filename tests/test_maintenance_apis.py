import json
import pytest
import six

from etcd3.models import etcdserverpbAlarmType
from .envs import NO_DOCKER_SERVICE


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_hash(client):
    assert client.hash().hash


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_status(client):
    assert client.status().version


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_defragment(client):
    assert client.defragment()


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_alarm(client):
    assert client.alarm_activate(0, etcdserverpbAlarmType.NOSPACE)
    assert client.alarm_get(0, etcdserverpbAlarmType.NOSPACE)
    assert client.alarm_deactivate(0, etcdserverpbAlarmType.NOSPACE)


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_snapshot(client, etcd_cluster):
    # write some data into etcd
    for i in range(10):
        etcd_cluster.etcdctl('put key value%s' % i)
    out = etcd_cluster.etcdctl('-w json put some thing')
    if six.PY3:  # pragma: no cover
        out = six.text_type(out, encoding='utf-8')
    rev = json.loads(out)['header']['revision']
    etcd_cluster.etcdctl('compaction --physical %s' % (rev - 10))
    etcd_cluster.etcdctl('defrag')

    r = client.snapshot()
    with open('/tmp/etcd-snap.db', 'wb') as f:
        for i in r:
            assert i.blob
            f.write(i.blob)
    assert etcd_cluster.etcdctl('snapshot status /tmp/etcd-snap.db')
