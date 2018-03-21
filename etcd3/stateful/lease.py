"""
Sync lease util
"""
import logging
import threading
import time

from ..errors import ErrLeaseNotFound
from ..utils import retry

log = logging.getLogger('etcd3.Lease')


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
        self._thread = None

    @property
    def ID(self):
        return self._ID

    def grant(self):
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
        return self.client.lease_time_to_live(self.ID, keys=keys)

    def ttl(self):
        r = self.time_to_live()
        if 'TTL' not in r:
            return -1
        return r.TTL

    def alive(self):
        return self.ttl() > 0

    def keepalive_once(self):
        return self.client.lease_keep_alive_once(self.ID)

    refresh = keepalive_once

    def keepalive(self, keep_cb=None, cancel_cb=None):
        self.keeping = True

        def keepalived():
            while self.keeping:
                retry(lambda: self.keepalive_once(), max_tries=3, log=log)
                self.last_keep = time.time()
                log.debug("keeping lease %d" % self.ID)
                if keep_cb:
                    try:
                        keep_cb()
                    except Exception:
                        log.exception("stream_cb() raised an error")
                for i in range(int(self.grantedTTL / 2.0)):  # keep per grantedTTL/4 seconds
                    if self.keeping:
                        break
                    time.sleep(0.5)
            log.debug("canceled keeping lease %d" % self.ID)
            if cancel_cb:
                try:
                    cancel_cb()
                except Exception:
                    log.exception("cancel_cb() raised an error")

        t = self._thread = threading.Thread(target=keepalived)
        t.setDaemon(True)
        t.start()

    def cancel_keepalive(self, join=True):
        self.keeping = False
        if join and self._thread and self._thread.is_alive():
            self._thread.join()

    def jammed(self):
        """
        if is failed to keepalive
        """
        if not self.keeping:
            return False
        return time.time() - self.last_keep > self.grantedTTL / 4.0

    def revoke(self):
        self.cancel_keepalive(False)
        return self.client.lease_revoke(self.ID)

    def __enter__(self):
        self.grant()
        self.keepalive()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cancel_keepalive()
        self.revoke()
