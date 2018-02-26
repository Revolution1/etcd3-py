from .base import BaseAPI


class AuthAPI(BaseAPI):
    def authenticate(self, name, password):
        """
        Authenticate processes an authenticate request.

        :type name: str
        :param name: None
        :type password: str
        :param password: None
        """
        method = '/v3alpha/auth/authenticate'
        data = {}
        return self.call_rpc(method, data=data)

    def auth_disable(self):
        """
        AuthDisable disables authentication.

        """
        method = '/v3alpha/auth/disable'
        data = {}
        return self.call_rpc(method, data=data)

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
        data = {}
        return self.call_rpc(method, data=data)

    def role_delete(self, role):
        """
        RoleDelete deletes a specified role.

        :type role: str
        :param role: None
        """
        method = '/v3alpha/auth/role/delete'
        data = {}
        return self.call_rpc(method, data=data)

    def role_get(self, role):
        """
        RoleGet gets detailed role information.

        :type role: str
        :param role: None
        """
        method = '/v3alpha/auth/role/get'
        data = {}
        return self.call_rpc(method, data=data)

    def role_grant_permission(self, name, perm):
        """
        RoleGrantPermission grants a permission of a specified key or range to a specified role.

        :type name: str
        :param name: name is the name of the role which will be granted the permission.
        :type perm: dict
        :param perm: Permission is a single entity
        """
        method = '/v3alpha/auth/role/grant'
        data = {}
        return self.call_rpc(method, data=data)

    def role_list(self):
        """
        RoleList gets lists of all roles.

        """
        method = '/v3alpha/auth/role/list'
        data = {}
        return self.call_rpc(method, data=data)

    def role_revoke_permission(self, role, key, range_end):
        """
        RoleRevokePermission revokes a key or range permission of a specified role.

        :type role: str
        :param role: None
        :type key: str
        :param key: None
        :type range_end: str
        :param range_end: None
        """
        method = '/v3alpha/auth/role/revoke'
        data = {}
        return self.call_rpc(method, data=data)

    def user_add(self, name, password):
        """
        UserAdd adds a new user.

        :type name: str
        :param name: None
        :type password: str
        :param password: None
        """
        method = '/v3alpha/auth/user/add'
        data = {}
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
        data = {}
        return self.call_rpc(method, data=data)

    def user_delete(self, name):
        """
        UserDelete deletes a specified user.

        :type name: str
        :param name: name is the name of the user to delete.
        """
        method = '/v3alpha/auth/user/delete'
        data = {}
        return self.call_rpc(method, data=data)

    def user_get(self, name):
        """
        UserGet gets detailed user information.

        :type name: str
        :param name: None
        """
        method = '/v3alpha/auth/user/get'
        data = {}
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
        data = {}
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
        :param name: None
        :type role: str
        :param role: None
        """
        method = '/v3alpha/auth/user/revoke'
        data = {}
        return self.call_rpc(method, data=data)
