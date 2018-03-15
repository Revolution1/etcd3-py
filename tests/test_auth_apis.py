import pytest

from etcd3.client import Client
from etcd3.errors import ErrAuthNotEnabled
from etcd3.errors import ErrRoleNotFound
from etcd3.errors import ErrRootUserNotExist
from etcd3.errors import ErrUserNotFound
from etcd3.models import authpbPermissionType
from etcd3.utils import incr_last_byte
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


def teardown_auth():
    """
    disable auth, delete all users and roles
    """
    etcdctl('--user root:root auth disable', raise_error=False)
    etcdctl('--user root:changed auth disable', raise_error=False)
    for i in (etcdctl('role list', raise_error=False) or '').splitlines():
        etcdctl('role', 'delete', i)
    for i in (etcdctl('user list', raise_error=False) or '').splitlines():
        etcdctl('user', 'delete', i)


def enable_auth():
    etcdctl('user add root:root')
    etcdctl('role add root')
    etcdctl('user grant root root')
    etcdctl('auth enable')


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
def test_auth_flow(client, request):
    teardown_auth()
    request.addfinalizer(teardown_auth)

    # test error
    with pytest.raises(ErrRootUserNotExist):
        client.auth_enable()
    with pytest.raises(ErrAuthNotEnabled):
        client.authenticate('root', 'root')

    # test role add and get and list
    client.role_add('root')
    assert client.role_get('root')
    assert 'root' in client.role_list().roles

    # test role permission grant
    client.role_grant_permission('root', '/', permType=authpbPermissionType.READWRITE, prefix=True)
    r = client.role_get('root')
    assert len(r.perm) == 1
    # TODO: extract reqresp models and make enum enum
    assert r.perm[0].permType == authpbPermissionType.READWRITE.value
    assert r.perm[0].key == b'/'
    assert r.perm[0].range_end == incr_last_byte(b'/')

    # test role permission revoke
    client.role_revoke_permission('root', '/', prefix=True)
    r = client.role_get('root')
    assert 'perm' not in r

    # test user add
    client.user_add('root', 'root')
    assert client.user_get('root')
    assert 'root' in client.user_list().users

    # test user grant role
    client.user_grant_role('root', 'root')
    r = client.user_get('root')
    assert len(r.roles) == 1
    assert r.roles[0] == 'root'

    # test auth enable
    client.auth_enable()
    r = client.authenticate('root', 'root')
    assert r.token

    # test client auth
    client.auth('root', 'root')
    assert client.token
    assert client.user_get('root')

    # test user change password
    client.user_change_password('root', 'changed')
    client.auth('root', 'changed')
    client.user_change_password('root', 'root')
    client.auth('root', 'root')

    # test auth disable
    client.auth_disable()
    with pytest.raises(ErrAuthNotEnabled):
        client.authenticate('root', 'root')

    # test user revoke role
    client.user_revoke_role('root', 'root')
    r = client.user_get('root')
    assert 'roles' not in r

    # test role delete
    client.role_delete('root')
    with pytest.raises(ErrRoleNotFound):
        assert client.role_get('root')

    # test user delete
    client.user_delete('root')
    with pytest.raises(ErrUserNotFound):
        assert client.user_delete('root')
