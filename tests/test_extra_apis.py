import pytest

from etcd3.client import Client
from .envs import protocol, host, port
from .mocks import fake_request


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    c = Client(host, port, protocol)
    yield c
    c.close()


def test_version_api(client, monkeypatch):
    s = b'{"etcdserver":"3.3.0-rc.4","etcdcluster":"3.3.0"}'
    monkeypatch.setattr(client._session, 'get', fake_request(200, s))
    v = client.version()
    assert v.etcdserver == "3.3.0-rc.4"
    assert v.etcdcluster == "3.3.0"
