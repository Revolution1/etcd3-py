import os
import socket
import tempfile
import uuid

import six

from .watch import EventType
from ..errors import ErrLeaseNotFound
from ..utils import get_ident
from ..utils import log


class EtcdLockError(Exception):
    pass


class EtcdLockAcquireTimeout(Exception):
    pass


class Lock(object):  # TODO: maybe we could improve the performance by reduce some HTTP requests
    """
    Locking recipe for etcd, inspired by the kazoo recipe for zookeeper
    """

    DEFAULT_LOCK_TTL = 60

    HOST = 'host'
    PROCESS = 'process'
    THREAD = 'thread'

    def __init__(self, client, lock_name, lock_ttl=DEFAULT_LOCK_TTL, reentrant=None, lock_prefix='_locks'):
        """
        :type client: BaseClient
        :param client: instance of etcd.Client
        :type lock_name: str
        :param lock_name: the name of the lock
        :type lock_ttl: int
        :param lock_ttl: ttl of the lock, default is 60s
        :type reentrant: str
        :param reentrant: the reentrant type of the lock can set to Lock.HOST, Lock.PROCESS, Lock.THREAD
        :type lock_prefix: str
        :param lock_prefix: the prefix of the lock key
        """
        self.client = client
        self.name = lock_name
        self.lock_ttl = lock_ttl
        self.lock_prefix = lock_prefix
        self.reentrant = reentrant
        self.uuid = self._get_uuid()
        if six.PY3 and isinstance(self.uuid, str):
            self.uuid = six.binary_type(self.uuid, encoding='utf-8')
        self.lock_key = "{}/{}".format(lock_prefix, lock_name)  # the key of the lock
        self.holders_key = self.lock_key + '/holders'  # the key of holders-count
        self.is_taken = False  # if the lock is taken by someone
        self.lease = None
        self.__holders_lease = None
        self._watcher = None
        log.debug("Initiating lock for %s with uuid %s", self.lock_key, self.uuid)

    def _get_uuid(self):
        hostname = socket.gethostname()
        if self.reentrant is None:
            return '%s:%s' % (hostname, uuid.uuid4().hex[:8])
        elif self.reentrant == self.PROCESS:
            return '%s:proc:%s' % (hostname, os.getpid())
        elif self.reentrant == self.THREAD:
            return '%s:thrd:%s' % (hostname, get_ident())
        elif self.reentrant == self.HOST:
            return self._get_global_uuid('%s:host:%s' % (hostname, socket.gethostbyname(hostname)))
        else:
            raise TypeError("unknown reentrant type, expect one of Lock.HOST, Lock.PROCESS, Lock.THREAD")

    def _get_global_uuid(self, uuid):
        path = tempfile.gettempdir() + '/' + self.name + '_lock'
        while os.path.isdir(path):
            path = path + '_'
        if not os.path.exists(path):
            log.debug("writing host-global uuid to %s" % path)
            with open(path, 'w') as f:
                f.write(uuid)
            return uuid
        else:
            log.debug("reading host-global uuid from %s" % path)
            with open(path, 'rb') as f:
                return f.read()

    def _get_locker(self):
        r = self.client.range(self.lock_key).kvs
        return r[0] if r else None

    def _holders_lease(self):
        if self.__holders_lease:
            return self.__holders_lease
        locker = self._get_locker()
        if locker:
            self.__holders_lease = locker.lease
        return self.__holders_lease

    def holders(self):
        """
        tell how many holders are holding the lock

        :return: int
        """
        if not self.reentrant:
            if self._get_locker():
                return 1
            return 0
        r = self.client.range(self.holders_key).kvs
        if r is not None:
            self.__holders_lease = r[0].lease
            return int(r[0].value)
        lease = self._holders_lease()
        if lease:
            try:
                log.debug("try creating holders count key with lease %d" % lease)
                self.client.put(self.holders_key, b'%d' % 0, lease=lease)
            except ErrLeaseNotFound:
                self.__holders_lease = None
        return 0

    def incr_holder(self):
        """
        Atomic increase the holder count by 1
        """
        n = self.holders()
        t = self.client.Txn()
        t.If(t.key(self.holders_key).value == b'%d' % n)
        t.Then(t.put(self.holders_key, b'%d' % (n + 1), lease=self._holders_lease()))
        r = t.commit()
        if r.succeeded:
            return n + 1
        log.debug("failed to incr holders count")

    def decr_holder(self):
        """
        Atomic decrease the holder count by 1
        """
        n = self.holders() or 0
        t = self.client.Txn()
        t.If(t.key(self.holders_key).value == b'%d' % n)
        if n - 1 == 0:
            t.Then(t.delete(self.holders_key))
        else:
            t.Then(t.put(self.holders_key, b'%d' % (n - 1), lease=self._holders_lease()))
        r = t.commit()
        if r.succeeded:
            return n - 1
        log.debug("failed to decr holders count")

    @property
    def is_acquired(self):
        """
        if the lock is acquired
        """
        if not self.is_taken:
            log.debug("Lock not taken")
            return False
        locker = self._get_locker()
        if locker:
            self.is_taken = True
        if locker and locker.value == self.uuid:
            if self.lease and self.lease.keeping:
                return True
        return False

    acquired = is_acquired

    def acquire(self, block=True, lock_ttl=None, timeout=None, delete_key=True):
        """
        Acquire the lock.

        :type block: bool
        :param block: Block until the lock is obtained, or timeout is reached [default: True]
        :type lock_ttl: int
        :param lock_ttl: The duration of the lock we acquired, set to None for eternal locks
        :type timeout: int
        :param timeout: The time to wait before giving up on getting a lock
        :type delete_key: bool
        :param delete_key: whether delete the key if it has not attached to any lease [default: True]
        """
        lock_ttl = self.lock_ttl = lock_ttl or self.lock_ttl
        locker = self._get_locker()
        if locker:
            if not locker.lease:
                if not delete_key:
                    raise EtcdLockError("lock-key %s already exist but with no lease attached")
                log.debug("delete lock key that has no expiration")
                self.client.delete_range(locker.key)
            elif locker.value == self.uuid:
                log.debug("we already have the lock")
                if not (self.lease and self.lease.keeping):
                    log.debug("we have the lock but not keeping it, now keep the lease alive")
                    self.__holders_lease = None
                    self.lease = self.client.Lease(self.lock_ttl, locker.lease, new=False)
                    self.lease.grant()
                    self.lease.keepalive()
                    if self.reentrant:
                        log.debug("the lock is reentrant, will incr its holders count")
                        self.incr_holder()
                    self.is_taken = True
                return self
            elif block:
                event = self.wait(locker=locker, timeout=timeout)
                if not event:
                    log.debug("lock acquire wait timeout")
                    raise EtcdLockAcquireTimeout
            else:
                self.is_taken = True
                return
        # locker key not found
        log.debug("writing lock key to %s", self.lock_key)
        if self.lease and self.lease.keeping:  # clean old lease that may exist
            self.lease.revoke()
            self.__holders_lease = None
        self.lease = self.client.Lease(self.lock_ttl)
        self.lease.grant()
        txn = self.client.Txn()
        txn.If(txn.key(self.lock_key).value == self.uuid)
        txn.Else(txn.put(self.lock_key, self.uuid, lease=self.lease.ID))
        r = txn.commit()
        if r.succeeded:
            return self.acquire(block, lock_ttl, timeout, delete_key)
        else:
            self.is_taken = True
            self.lease.keepalive()
            if self.reentrant:
                log.debug("the lock is reentrant, will incr its holders count")
                self.incr_holder()
            log.debug("Lock key written, we got the lock")
        log.debug("Lock acquired (lock_key: %s, value: %s)" % (self.lock_key, self.uuid))
        return self

    def wait(self, locker=None, timeout=None):
        """
        Wait until the lock is lock is able to acquire

        :param locker: kv of the lock
        :param timeout: wait timeout
        """
        locker = locker or self._get_locker()
        if not locker:
            return
        self._watcher = watcher = self.client.Watcher(key=locker.key, max_retries=0)
        return watcher.watch_once(lambda e: e.type == EventType.DELETE or e.value == self.uuid, timeout=timeout)

    def release(self):
        """
        Release the lock
        """
        if self.reentrant:
            n = self.decr_holder()
            if n is not None and n == 0:
                self.lease.revoke()
                self.lease = None
                self.is_taken = False
            else:
                self.lease.cancel_keepalive(join=False)
                self.lease = None
                self.is_taken = True
        else:
            self.lease.revoke()
            self.lease = None
            self.is_taken = False
        log.debug("Lock released (lock_key: %s, value: %s)" % (self.lock_key, self.uuid))

    def __enter__(self):
        """
        You can use the lock as a contextmanager
        """
        self.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self.release()
        return False
