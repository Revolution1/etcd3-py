import pytest

from etcd3.client import Etcd3APIClient
from mocks import fake_request
from .envs import protocol, host, port


@pytest.fixture(scope='session')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    c = Etcd3APIClient(host, port, protocol)
    yield c
    c.close()


def test_version_api(client, monkeypatch):
    s = b'{"etcdserver":"3.3.0-rc.4","etcdcluster":"3.3.0"}'
    monkeypatch.setattr(client.session, 'get', fake_request(200, s, client.response_class))
    v = client.version()
    assert v.etcdserver == "3.3.0-rc.4"
    assert v.etcdcluster == "3.3.0"
