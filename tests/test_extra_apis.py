import pytest

from etcd3.client import Client
from tests.docker_cli import docker_run_etcd_main
from .envs import protocol, host
from .mocks import fake_request


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    _, p, _ = docker_run_etcd_main()
    c = Client(host, p, protocol)
    yield c
    c.close()


def test_version_api(client, monkeypatch):
    s = b'{"etcdserver":"3.3.0-rc.4","etcdcluster":"3.3.0"}'
    monkeypatch.setattr(client._session, 'get', fake_request(200, s))
    v = client.version()
    assert v.etcdserver == "3.3.0-rc.4"
    assert v.etcdcluster == "3.3.0"


def test_health_api(client):
    assert client.health()
