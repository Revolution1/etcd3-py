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
            r = self.client.lease_time_to_live(self.ID)
            if r.TTL == -1:
                raise ErrLeaseNotFound
            self.last_grant = time.time() - r.TTL
            return r

    def time_to_live(self, keys=False):
        return self.client.lease_time_to_live(self.ID, keys=keys)

    def ttl(self):
        return self.time_to_live().TTL

    def alive(self):
        return self.ttl() > 0

    def keepalive_once(self):
        return self.client.lease_keep_alive_once(self.ID)

    refresh = keepalive_once

    # def keepalive(self, stream_cb=None, cancel_cb=None):
    #     self.fifo = produce_stream(b'{"ID":%d}\n' % self.ID, self.grantedTTL / 4.0,
    #                                stream_cb=stream_cb, cancel_cb=cancel_cb)
    #     self.stream_conn = self.client.lease_keep_alive(self.fifo)
    #     return self.stream_conn

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
                time.sleep(self.grantedTTL / 4.0)
            log.debug("canceled keeping lease %d" % self.ID)
            if cancel_cb:
                try:
                    cancel_cb()
                except Exception:
                    log.exception("cancel_cb() raised an error")

        t = self._thread = threading.Thread(target=keepalived)
        t.setDaemon(True)
        t.start()

    def cancel_keepalive(self):
        self.keeping = False

    def jammed(self):
        """
        if is failed to keepalive
        """
        if not self.keeping:
            return False
        return time.time() - self.last_keep > self.grantedTTL / 4.0

    def revoke(self):
        return self.client.lease_revoke(self.ID)

    def __enter__(self):
        self.grant()
        self.keepalive()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cancel_keepalive()
        self.revoke()

# def produce_stream(data, interval, q=None, stream_cb=None, cancel_cb=None):
#     """
#     :param data: data to put into stream
#     :param interval: put interval
#     :param q: queue that handles put
#     :param stream_cb: callback when put
#     :param cancel_cb: callback when stream canceled
#     :return: StreamFIFO
#     """
#     q = q or StreamFIFO(maxsize=128)
#
#     def _put():
#         while True:
#             try:
#                 q.put(data)
#                 log.debug("produced a stream chunk")
#                 if stream_cb:
#                     stream_cb()
#                 time.sleep(interval)
#             except StreamClosed:
#                 log.debug("exiting due to stream closed")
#                 if cancel_cb:
#                     cancel_cb()
#                 break
#             except Exception as e:
#                 raise
#
#     t = threading.Thread(target=_put)
#     t.setDaemon(True)
#     t.start()
#     return q


# class StreamClosed(ValueError):
#     pass


# class StreamFIFO(Queue):
#     def __init__(self, maxsize=0):
#         super(StreamFIFO, self).__init__(maxsize=maxsize)
#         self._closed = False
#         self.last_get = None
#
#     @property
#     def closed(self):
#         return self._closed
#
#     def put(self, item, block=True, timeout=None):
#         if self.closed:
#             raise StreamClosed("put on a closed stream")
#         return super(StreamFIFO, self).put(item, block, timeout)
#
#     def get(self, block=True, timeout=None):
#         if self.closed:
#             raise StreamClosed("get on a closed stream")
#         self.last_get = time.time()
#         return super(StreamFIFO, self).get(block, timeout)
#
#     def __iter__(self):
#         r = self.get()
#         if not r:
#             raise StopIteration
#         yield r
#
#     def close(self):
#         self.queue.clear()
#         self._closed = True

# def read(self, n):
#     return self.get()
