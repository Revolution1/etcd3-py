from .base import BaseAPI


class LockAPI(BaseAPI):
    def lock(self, name, lease=0):
        """
        Lock acquires a distributed shared lock on a given named lock.
        On success, it will return a unique key that exists so long as
        the lock is held by the caller. This key can be used in
        conjunction with transactions to safely ensure updates to etcd
        only occur while holding lock ownership. The lock is held until
        Unlock is called on the key or the lease associate with the
        owner expires.

        :type name: str
        :param name: name is the identifier for the distributed shared lock to be acquired.
        :type lease: int
        :param lease: lease is the lease ID to associate with the key in the key-value store. A lease
            value of 0 indicates no lease.
        """

        method = '/lock/lock'
        data = {
            "name": name,
            "lease": lease
        }
        return self.call_rpc(method, data=data)

    def unlock(self, key):
        """
        Unlock takes a key returned by Lock and releases the hold on
        lock. The next Lock caller waiting for the lock will then be
        woken up and given ownership of the lock.

        :type key: str or bytes
        :param key: key is the lock ownership key granted by Lock.
        :type lease: int
        :param lease: lease is the lease ID to associate with the key in the key-value store. A lease
            value of 0 indicates no lease.
        """

        method = '/lock/unlock'
        data = {
            "key": key,
        }
        return self.call_rpc(method, data=data)
