import pytest

from etcd3.client import Client
from .envs import protocol, host, port
from .etcd_go_cli import etcdctl, NO_ETCD_SERVICE


@pytest.fixture(scope='module')
def client():
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    c = Client(host, port, protocol)
    yield c
    c.close()


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_authentication(client, request):
    def teardown():
        etcdctl('--user root:root auth disable', raise_error=False)
        etcdctl('--user root:root role delete root', raise_error=False)
        etcdctl('--user root:root user delete root', raise_error=False)

    request.addfinalizer(teardown)

    teardown()
    etcdctl('user add root:root')
    etcdctl('role add root')
    etcdctl('user grant root root')
    etcdctl('auth enable')
    r = client.authenticate('root', 'root')
    assert r.token
