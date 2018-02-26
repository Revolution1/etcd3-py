import pytest
import six

from etcd3.client import Etcd3APIClient
from etcd3.errors import Etcd3APIError
from .envs import protocol, host, port
from .etcd_go_cli import etcdctl


@pytest.fixture()
def client():
    c = Etcd3APIClient(host, port, protocol)
    yield c
    c.close()


def test_request_and_model(client):
    etcdctl('put test_key test_value')
    result = client.call_rpc('/v3alpha/kv/range', {'key': 'test_key'})
    # {"header":{"cluster_id":11588568905070377092,"member_id":128088275939295631,"revision":3,"raft_term":2},"kvs":[{"key":"dGVzdF9rZXk=","create_revision":3,"mod_revision":3,"version":1,"value":"dGVzdF92YWx1ZQ=="}],"count":1}'
    if six.PY2:
        assert result.kvs[0].key == 'test_key'
        assert result.kvs[0].value == 'test_value'
    else:
        assert result.kvs[0].key == b'test_key'
        assert result.kvs[0].value == b'test_value'
    etcdctl('del test_key')


def test_stream(client):
    r = client.call_rpc('/v3alpha/watch', {'create_request': {'key': 'test_key'}}, stream=True)
    times = 3
    header_times = 1
    for i in r:
        if not times:
            break
        etcdctl('put test_key test_value')
        if hasattr(i, 'events'):
            if six.PY2:
                assert i.events[0].kv.key == 'test_key'
                assert i.events[0].kv.value == 'test_value'
            else:
                assert i.events[0].kv.key == b'test_key'
                assert i.events[0].kv.value == b'test_value'
            times -= 1
        else:
            header_times -= 1
            assert header_times >= 0
    r.close()


def test_exception(client):
    with pytest.raises(Etcd3APIError, match=r".*'Not Found'.*"):
        client.call_rpc('/v3alpha/kv/rang', {'key': 'foa'})
