from .base import BaseAPI


class LeaseAPI(BaseAPI):
    def lease_revoke(self, ID):
        """
        LeaseRevoke revokes a lease. All keys attached to the lease will expire and be deleted.

        :type ID: int
        :param ID: ID is the lease ID to revoke. When the ID is revoked, all associated keys will be deleted.
        """
        method = '/v3alpha/kv/lease/revoke'
        data = {
            "ID": ID
        }
        return self.call_rpc(method, data=data)

    def lease_time_to_live(self, ID, keys=False):
        """
        LeaseTimeToLive retrieves lease information.

        :type ID: int
        :param ID: ID is the lease ID for the lease.
        :type keys: bool
        :param keys: keys is true to query all the keys attached to this lease.
        """
        method = '/v3alpha/kv/lease/timetolive'
        data = {
            "ID": ID,
            "keys": keys
        }
        return self.call_rpc(method, data=data)

    def lease_grant(self, TTL, ID=0):
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
        data = {
            "TTL": TTL,
            "ID": ID
        }
        return self.call_rpc(method, data=data)

    # TODO: stream keepalive with context
    # http://docs.python-requests.org/en/master/user/advanced/#chunk-encoded-requests
    def lease_keep_alive(self, ID):
        """
        PLEASE USE THE Transaction util

        LeaseKeepAlive keeps the lease alive by streaming keep alive requests from the client
        to the server and streaming keep alive responses from the server to the client.

        :type ID: int
        :param ID: ID is the lease ID for the lease to keep alive.
        """
        method = '/v3alpha/lease/keepalive'
        data = {
            "ID": ID
        }
        return self.call_rpc(method, data=data, stream=True)

    def lease_keep_alive_once(self, ID):
        """
        this api only send keep alive once instead of streaming send multiple IDs

        LeaseKeepAlive keeps the lease alive by streaming keep alive requests from the client
        to the server and streaming keep alive responses from the server to the client.

        :type ID: int
        :param ID: ID is the lease ID for the lease to keep alive.
        """

        for i in self.lease_keep_alive(ID):
            return i
