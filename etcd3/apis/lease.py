from .base import BaseAPI


class LeaseAPI(BaseAPI):
    def lease_revoke(self, ID):
        """
        LeaseRevoke revokes a lease. All keys attached to the lease will expire and be deleted.

        :type ID: int
        :param ID: ID is the lease ID to revoke. When the ID is revoked, all associated keys will be deleted.
        """
        method = '/v3alpha/kv/lease/revoke'
        data = {}
        return self.call_rpc(method, data=data)

    def lease_time_to_live(self, ID, keys):
        """
        LeaseTimeToLive retrieves lease information.

        :type ID: int
        :param ID: ID is the lease ID for the lease.
        :type keys: bool
        :param keys: keys is true to query all the keys attached to this lease.
        """
        method = '/v3alpha/kv/lease/timetolive'
        data = {}
        return self.call_rpc(method, data=data)

    def lease_grant(self, TTL, ID):
        """
        LeaseGrant creates a lease which expires if the server does not receive a keepAlive
        within a given time to live period. All keys attached to the lease will be expired and
        deleted if the lease expires. Each expired key generates a delete event in the event history.

        :type TTL: int
        :param TTL: TTL is the advisory time-to-live in seconds.
        :type ID: int
        :param ID: ID is the requested ID for the lease. If ID is set to 0, the lessor chooses an ID.
        """
        method = '/v3alpha/lease/grant'
        data = {}
        return self.call_rpc(method, data=data)

    def lease_keep_alive(self, ID):
        """
        LeaseKeepAlive keeps the lease alive by streaming keep alive requests from the client
        to the server and streaming keep alive responses from the server to the client.

        :type ID: int
        :param ID: ID is the lease ID for the lease to keep alive.
        """
        method = '/v3alpha/lease/keepalive'
        data = {}
        return self.call_rpc(method, data=data)
