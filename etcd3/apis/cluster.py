from .base import BaseAPI


class ClusterAPI(BaseAPI):
    def member_add(self, peerURLs):
        """
        MemberAdd adds a member into the cluster.

        :type peerURLs: list of str
        :param peerURLs: peerURLs is the list of URLs the added member will use to communicate with the cluster.
        """
        method = '/v3alpha/cluster/member/add'
        data = {
            "peerURLs": peerURLs
        }
        return self.call_rpc(method, data=data)

    def member_list(self):
        """
        MemberList lists all the members in the cluster.

        """
        method = '/v3alpha/cluster/member/list'
        data = {}
        return self.call_rpc(method, data=data)

    def member_remove(self, ID):
        """
        MemberRemove removes an existing member from the cluster.

        :type ID: int
        :param ID: ID is the member ID of the member to remove.
        """
        method = '/v3alpha/cluster/member/remove'
        data = {
            "ID": ID
        }
        return self.call_rpc(method, data=data)

    def member_update(self, ID, peerURLs):
        """
        MemberUpdate updates the member configuration.

        :type ID: int
        :param ID: ID is the member ID of the member to update.
        :type peerURLs: list of str
        :param peerURLs: peerURLs is the new list of URLs the member will use to communicate with the cluster.
        """
        method = '/v3alpha/cluster/member/update'
        data = {
            "ID": ID,
            "peerURLs": peerURLs
        }
        return self.call_rpc(method, data=data)
