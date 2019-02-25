import pytest
from etcd3.errors import Etcd3Exception
from etcd3 import Client
from .envs import CA_PATH, CERT_PATH, KEY_PATH
from .envs import NO_DOCKER_SERVICE
from .mocks import fake_request


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_request_and_model(client, etcd_cluster):
    etcd_cluster.etcdctl('put test_key test_value')
    result = client.call_rpc('/kv/range', {'key': 'test_key'})
    # {"header":{"cluster_id":11588568905070377092,"member_id":128088275939295631,"revision":3,"raft_term":2},"kvs":[{"key":"dGVzdF9rZXk=","create_revision":3,"mod_revision":3,"version":1,"value":"dGVzdF92YWx1ZQ=="}],"count":1}'
    assert result.kvs[0].key == b'test_key'
    assert result.kvs[0].value == b'test_value'
    etcd_cluster.etcdctl('del test_key')


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_stream(client, etcd_cluster):
    times = 20
    created = False
    with client.call_rpc('/watch', {'create_request': {'key': 'test_key'}}, stream=True) as r:
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


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_request_exception(client):
    with pytest.raises(Etcd3Exception, match=r".*'Not Found'.*"):
        client.call_rpc('/kv/rag', {})  # non exist path


def test_patched_stream(client, monkeypatch):
    s = b'{"result": {"header": {"raft_term": 7, "member_id": 128088275939295631, "cluster_id": 11588568905070377092, "revision": 378}, "created": true}}' \
        b'{"result": {"header": {"raft_term": 7, "member_id": 128088275939295631, "cluster_id": 11588568905070377092, "revision": 379}, "events": [{"kv": {"mod_revision": 379, "value": "dGVzdF92YWx1ZQ==", "create_revision": 379, "version": 1, "key": "dGVzdF9rZXk="}}]}}' \
        b'{"result": {"header": {"raft_term": 7, "member_id": 128088275939295631, "cluster_id": 11588568905070377092, "revision": 380}, "events": [{"kv": {"mod_revision": 380, "value": "dGVzdF92YWx1ZQ==", "create_revision": 379, "version": 2, "key": "dGVzdF9rZXk="}}]}}' \
        b'{"result": {"header": {"raft_term": 7, "member_id": 128088275939295631, "cluster_id": 11588568905070377092, "revision": 381}, "events": [{"kv": {"mod_revision": 381, "value": "dGVzdF92YWx1ZQ==", "create_revision": 379, "version": 3, "key": "dGVzdF9rZXk="}}]}}' \
        b'{"result": {"header": {"raft_term": 7, "member_id": 128088275939295631, "cluster_id": 11588568905070377092, "revision": 381}, "events": [{"kv": {"mod_revision": 381, "value": "dGVzdF92YWx1ZQ==", "create_revision": 379, "version": 3, "key": "dGVzdF9rZXk="}}]}}'
    post = fake_request(200, s)
    monkeypatch.setattr(client._session, 'post', post)
    times = 3
    created = False
    with client.call_rpc('/watch', {'create_request': {'key': 'test_key'}}, stream=True) as r:
        for i in r:
            if not times:  # pragma: no cover
                break
            if not created:
                created = i.created
                assert created
            if i.events:
                assert i.events[0].kv.key == b'test_key'
                assert i.events[0].kv.value == b'test_value'
                times -= 1


def test_patched_request_and_model(client, monkeypatch):
    s = b'{"header":{"cluster_id":11588568905070377092,"member_id":128088275939295631,"revision":3,"raft_term":2},' \
        b'"kvs":[{"key":"dGVzdF9rZXk=","create_revision":3,"mod_revision":3,"version":1,"value":"dGVzdF92YWx1ZQ=="}],' \
        b'"count":1}'
    post = fake_request(200, s)
    monkeypatch.setattr(client._session, 'post', post)
    result = client.call_rpc('/kv/range', {'key': 'test_key'})
    assert post.call_args[1]['json']['key'] == 'dGVzdF9rZXk='
    assert result.kvs[0].key == b'test_key'
    assert result.kvs[0].value == b'test_value'


def test_patched_request_exception(client, monkeypatch):
    post = fake_request(404, 'Not Found')
    monkeypatch.setattr(client._session, 'post', post)
    with pytest.raises(Etcd3Exception, match=r".*'Not Found'.*"):
        client.call_rpc('/kv/rag', {})  # non exist path


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_client_ssl(etcd_cluster_ssl):
    client = Client(endpoints=etcd_cluster_ssl.get_endpoints(),
                    cert=(CERT_PATH, KEY_PATH), verify=CA_PATH)
    assert client.version()


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
def test_client_host_port(etcd_cluster_ssl):
    endpoint = etcd_cluster_ssl.get_endpoints()[0]
    client = Client(host=endpoint.host, port=endpoint.port,
                    cert=(CERT_PATH, KEY_PATH), verify=CA_PATH)
    assert client.version()
