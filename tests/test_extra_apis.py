from .mocks import fake_request


def test_version_api(client, monkeypatch):
    s = b'{"etcdserver":"3.3.0-rc.4","etcdcluster":"3.3.0"}'
    monkeypatch.setattr(client._session, 'get', fake_request(200, s))
    v = client.version()
    assert v.etcdserver == "3.3.0-rc.4"
    assert v.etcdcluster == "3.3.0"


def test_health_api(client):
    assert client.health()
