"""
Sync lease util
"""
import sys
import threading
import time

from ..errors import ErrLeaseNotFound
from ..utils import log
from ..utils import retry


class Lease(object):
    def __init__(self, client, ttl, ID=0, new=True):
        """
        :type client: BaseClient
        :param client: client instance of etcd3
        :type ID: int
        :param ID: ID is the requested ID for the lease. If ID is set to 0, the lessor chooses an ID.
        :type new: bool
        :param new: whether grant a new lease or maintain a exist lease by its id [default: True]
        """
        self.client = client
        if ttl < 2:
            ttl = 2
        self.grantedTTL = ttl
        if not new and not ID:
            raise TypeError("should provide the lease ID if new=False")
        self._ID = ID
        self.new = new
        self.last_grant = None
        self.keeping = False
        self.last_keep = None
        self._keepalive_error = None
        self._keepalive_exc_info = None
        self._keepalive_keep_cb_error = None
        self._keepalive_keep_cb_exc_info = None
        self._keepalive_cancel_cb_error = None
        self._keepalive_cancel_cb_exc_info = None
        self._thread = None
        self._lock = threading.Condition()

    @property
    def ID(self):
        """
        Property: the id of the granted lease

        :return: int
        """
        return self._ID

    def grant(self):
        """
        Grant the lease if new is set to False
        or it just inherit the lease of the specified id

        When granting new lease if ID is set to 0, the lessor will chooses an ID.
        """
        if self.new:
            r = self.client.lease_grant(self.grantedTTL, self.ID)
            self.last_grant = time.time()
            self._ID = r.ID
            return r
        else:
            r = self.time_to_live()
            if 'TTL' not in r:
                ttl = -1
            else:
                ttl = r.TTL
            if ttl == -1:
                raise ErrLeaseNotFound
            self.last_grant = time.time() - ttl
            return r

    def time_to_live(self, keys=False):
        """
        Retrieves lease information.

        :type keys: bool
        :param keys: whether return the keys that attached to the lease
        """
        return self.client.lease_time_to_live(self.ID, keys=keys)

    def ttl(self):
        """
        Get the ttl that lease has left

        :return: int
        """
        r = self.time_to_live()
        if 'TTL' not in r:
            return -1
        return r.TTL

    def alive(self):
        """
        Tell if the lease is still alive

        :return: bool
        """
        return self.ttl() > 0

    def keepalive_once(self):
        """
        Call keepalive for once to refresh the ttl of the lease
        """
        return self.client.lease_keep_alive_once(self.ID)

    refresh = keepalive_once

    def keepalive(self, keep_cb=None, cancel_cb=None):
        """
        Start a daemon thread to constantly keep the lease alive

        :type keep_cb: callable
        :param keep_cb: callback function that will be called after every refresh
        :type cancel_cb: callable
        :param cancel_cb: callback function that will be called after cancel keepalive
        """
        if self.keeping:
            raise RuntimeError("already keeping")
        self.keeping = True
        self._keepalive_error = None
        self._keepalive_exc_info = None

        def keepalived():
            try:
                with self._lock:
                    while self.keeping:
                        retry(self.keepalive_once, max_tries=3, log=log)
                        self.last_keep = time.time()
                        log.debug("keeping lease %d" % self.ID)
                        if keep_cb:
                            try:
                                keep_cb()
                            except Exception as e:
                                log.exception("keep_cb() raised an error")
                                self._keepalive_keep_cb_error = e
                                self._keepalive_keep_cb_exc_info = sys.exc_info()
                        for _ in range(int(self.grantedTTL / 2.0)):  # keep per grantedTTL/4 seconds
                            if not self.keeping:
                                break
                            self._lock.wait(0.5)
                    log.debug("canceled keeping lease %d" % self.ID)
                    if cancel_cb:
                        try:
                            cancel_cb()
                        except Exception as e:
                            log.exception("cancel_cb() raised an error")
                            self._keepalive_cancel_cb_error = e
                            self._keepalive_cancel_cb_exc_info = e
            except Exception as e:
                log.exception('error occurred while keeping alive lease')
                self._keepalive_error = e
                self._keepalive_exc_info = sys.exc_info()

        t = self._thread = threading.Thread(target=keepalived)
        t.setDaemon(True)
        t.start()

    def cancel_keepalive(self, join=True):
        """
        stop keeping-alive

        :type join: bool
        :param join: whether to wait the keepalive thread to exit
        """
        self.keeping = False
        with self._lock:
            self._lock.notify_all()
        if join and self._thread and self._thread.is_alive():
            self._thread.join()

    def jammed(self):
        """
        if is failed to keepalive at the last loop
        """
        if not self.keeping:
            return False
        return time.time() - self.last_keep > self.grantedTTL / 4.0

    def revoke(self):
        """
        revoke the lease
        """
        log.debug("revoking lease %d" % self.ID)
        self.cancel_keepalive(False)
        return self.client.lease_revoke(self.ID)

    def __enter__(self):
        self.grant()
        self.keepalive()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cancel_keepalive()
        self.revoke()
