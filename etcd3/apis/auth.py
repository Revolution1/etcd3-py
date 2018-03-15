from .base import BaseAPI
from ..models import authpbPermissionType
from ..utils import check_param, incr_last_byte


class AuthAPI(BaseAPI):
    def authenticate(self, name, password):
        """
        Authenticate processes an authenticate request.

        :type name: str
        :param name: name of the user
        :type password: str
        :param password: password of the user
        """
        method = '/v3alpha/auth/authenticate'
        data = {
            "name": name,
            "password": password
        }
        return self.call_rpc(method, data=data)

    def auth_disable(self):
        """
        AuthDisable disables authentication.

        """
        method = '/v3alpha/auth/disable'
        data = {}
        r = self.call_rpc(method, data=data)
        self.token = None  # clear local token
        return r

    def auth_enable(self):
        """
        AuthEnable enables authentication.

        """
        method = '/v3alpha/auth/enable'
        data = {}
        return self.call_rpc(method, data=data)

    def role_add(self, name):
        """
        RoleAdd adds a new role.

        :type name: str
        :param name: name is the name of the role to add to the authentication system.
        """
        method = '/v3alpha/auth/role/add'
        data = {
            "name": name
        }
        return self.call_rpc(method, data=data)

    def role_delete(self, role):
        """
        RoleDelete deletes a specified role.

        :type role: str
        :param role: None
        """
        method = '/v3alpha/auth/role/delete'
        data = {
            "role": role
        }
        return self.call_rpc(method, data=data)

    def role_get(self, role):
        """
        RoleGet gets detailed role information.

        :type role: str
        :param role: None
        """
        method = '/v3alpha/auth/role/get'
        data = {
            "role": role
        }
        return self.call_rpc(method, data=data)

    @check_param(at_least_one_of=['key', 'all'], at_most_one_of=['range_end', 'prefix', 'all'])
    def role_grant_permission(self, name, key=None, permType=authpbPermissionType.READ,
                              range_end=None, prefix=False, all=False):
        """
        RoleGrantPermission grants a permission of a specified key or range to a specified role.

        :type name: str
        :param name: name is the name of the role which will be granted the permission.
        :type key: str
        :param key: the key been granted to the role
        :type perm: dict
        :param perm: authpbPermissionType.READ or authpbPermissionType.WRITE or authpbPermissionType.READWRITE
        :type range_end: str
        :param range_end: range_end is the upper bound on the requested range [key, range_end).
            If range_end is '\0', the range is all keys >= key.
            If range_end is key plus one (e.g., "aa"+1 == "ab", "a\xff"+1 == "b"),
            then the range request gets all keys prefixed with key.
            If both key and range_end are '\0', then the range request returns all keys.
        :type prefix: bool
        :param prefix: if the key is a prefix [default: False]
        :type all: bool
        :param all: all the keys [default: False]
        """
        method = '/v3alpha/auth/role/grant'
        if all:
            key = range_end = '\0'
        if prefix:
            range_end = incr_last_byte(key)
        data = {
            "name": name,
            "perm": {
                "permType": permType,
                "key": key,
                "range_end": range_end
            }
        }
        data['perm'] = {k: v for k, v in data['perm'].items() if v is not None}
        return self.call_rpc(method, data=data)

    def role_list(self):
        """
        RoleList gets lists of all roles.
        """
        method = '/v3alpha/auth/role/list'
        data = {}
        return self.call_rpc(method, data=data)

    @check_param(at_least_one_of=['key', 'all'], at_most_one_of=['range_end', 'prefix', 'all'])
    def role_revoke_permission(self, role, key=None, range_end=None, prefix=False, all=False):
        """
        RoleRevokePermission revokes a key or range permission of a specified role.

        :type role: str
        :param role: the name of the role which will get permission revoked.
        :type key: str
        :param key: the key been revoked from the role
        :type range_end: str
        :param range_end: range_end is the upper bound on the requested range [key, range_end).
            If range_end is '\0', the range is all keys >= key.
            If range_end is key plus one (e.g., "aa"+1 == "ab", "a\xff"+1 == "b"),
            then the range request gets all keys prefixed with key.
            If both key and range_end are '\0', then the range request returns all keys.
        :type prefix: bool
        :param prefix: if the key is a prefix [default: False]
        :type all: bool
        :param all: all the keys [default: False]
        """
        method = '/v3alpha/auth/role/revoke'
        if all:
            key = range_end = '\0'
        if prefix:
            range_end = incr_last_byte(key)
        data = {
            "role": role,
            "key": key,
            "range_end": range_end
        }
        data = {k: v for k, v in data.items() if v is not None}
        return self.call_rpc(method, data=data)

    def user_add(self, name, password):
        """
        UserAdd adds a new user.

        :type name: str
        :param name: name of the user
        :type password: str
        :param password: password of the user
        """
        method = '/v3alpha/auth/user/add'
        data = {
            "name": name,
            "password": password
        }
        return self.call_rpc(method, data=data)

    def user_change_password(self, name, password):
        """
        UserChangePassword changes the password of a specified user.

        :type name: str
        :param name: name is the name of the user whose password is being changed.
        :type password: str
        :param password: password is the new password for the user.
        """
        method = '/v3alpha/auth/user/changepw'
        data = {
            "name": name,
            "password": password
        }
        return self.call_rpc(method, data=data)

    def user_delete(self, name):
        """
        UserDelete deletes a specified user.

        :type name: str
        :param name: name is the name of the user to delete.
        """
        method = '/v3alpha/auth/user/delete'
        data = {
            "name": name
        }
        return self.call_rpc(method, data=data)

    def user_get(self, name):
        """
        UserGet gets detailed user information.

        :type name: str
        :param name: name is the name of the user to get.
        """
        method = '/v3alpha/auth/user/get'
        data = {
            "name": name
        }
        return self.call_rpc(method, data=data)

    def user_grant_role(self, user, role):
        """
        UserGrant grants a role to a specified user.

        :type user: str
        :param user: user is the name of the user which should be granted a given role.
        :type role: str
        :param role: role is the name of the role to grant to the user.
        """
        method = '/v3alpha/auth/user/grant'
        data = {
            "user": user,
            "role": role
        }
        return self.call_rpc(method, data=data)

    def user_list(self):
        """
        UserList gets a list of all users.
        """
        method = '/v3alpha/auth/user/list'
        data = {}
        return self.call_rpc(method, data=data)

    def user_revoke_role(self, name, role):
        """
        UserRevokeRole revokes a role of specified user.

        :type name: str
        :param name: username to revoke
        :type role: str
        :param role: role name
        """
        method = '/v3alpha/auth/user/revoke'
        data = {
            "name": name,
            "role": role
        }
        return self.call_rpc(method, data=data)
