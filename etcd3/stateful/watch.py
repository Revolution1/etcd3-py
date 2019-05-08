import logging
import re
import socket
import threading
import time
from collections import deque

import six
from requests import ConnectionError
from requests.exceptions import ChunkedEncodingError

from ..errors import Etcd3WatchCanceled
from ..models import EventEventType
from ..utils import check_param
from ..utils import get_ident
from ..utils import log

EventType = EventEventType


class OnceTimeout(IOError):
    """
    Timeout caused by watch once
    """
    pass


class KeyValue(object):  # pragma: no cover
    """
    Model of the key-value of the event
    """

    def __init__(self, data):
        self._data = data
        self.key = data.get('key')
        self.create_revision = data.get('create_revision')
        self.mod_revision = data.get('mod_revision')
        self.value = data.get('value')
        self.lease = data.get('lease')

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __getitem__(self, item):
        return self._data.get(item)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, item):
        return item in self._data

    def __repr__(self):
        return "<KeyValue of '%s'>" % self.key


class Event(KeyValue):
    """
    Watch event
    """

    def __init__(self, data, header=None):
        """
        :param data: dict data of a etcdserverpbWatchResponse.events[<mvccpbEvent>]
        :param header: the header of etcdserverpbWatchResponse
        """
        super(Event, self).__init__(data.kv._data)
        self.header = header
        self.type = data.type or EventType.PUT  # default is PUT
        self._data['type'] = self.type
        self.prev_kv = None
        if 'prev_kv' in data:
            self.prev_kv = KeyValue(data.prev_kv._data)
        self._data['prev_kv'] = self.prev_kv

    def __repr__(self):
        return "<WatchEvent %s '%s'>" % (self.type.value, self.key)


class Watcher(object):
    @check_param(at_least_one_of=['key', 'all'], at_most_one_of=['range_end', 'prefix', 'all'])
    def __init__(self, client, max_retries=-1, key=None, range_end=None, start_revision=None, progress_notify=None,
                 prev_kv=None, prefix=None, all=None, no_put=False, no_delete=False):
        """
        Initialize a watcher

        :type client: BaseClient
        :param client: client instance of etcd3
        :type max_retries: int
        :param max_retries: max retries when watch failed due to network problem, -1 means no limit [default: -1]
        :type key: str or bytes
        :param key: key is the key to register for watching.
        :type range_end: str or bytes
        :param range_end: range_end is the end of the range [key, range_end) to watch. If range_end is not given,
            only the key argument is watched. If range_end is equal to '\0', all keys greater than
            or equal to the key argument are watched.
            If the range_end is one bit larger than the given key,
            then all keys with the prefix (the given key) will be watched.
        :type start_revision: int
        :param start_revision: start_revision is an optional revision to watch from (inclusive). No start_revision is "now".
        :type progress_notify: bool
        :param progress_notify: progress_notify is set so that the etcd server will periodically send a WatchResponse with
            no events to the new watcher if there are no recent events. It is useful when clients
            wish to recover a disconnected watcher starting from a recent known revision.
            The etcd server may decide how often it will send notifications based on current load.
        :type prev_kv: bool
        :param prev_kv: If prev_kv is set, created watcher gets the previous KV before the event happens.
            If the previous KV is already compacted, nothing will be returned.
        :type prefix: bool
        :param prefix: if the key is a prefix [default: False]
        :type all: bool
        :param all: all the keys [default: False]
        :type no_put: bool
        :param no_put: filter out the put events at server side before it sends back to the watcher. [default: False]
        :type no_delete: bool
        :param no_delete: filter out the delete events at server side before it sends back to the watcher. [default: False]
        """
        self.client = client
        self.revision = None
        self.watch_id = None
        self.retries = 0
        self.errors = deque(maxlen=20)
        if max_retries == -1:
            max_retries = 9223372036854775807  # maxint
        self.max_retries = max_retries
        self.callbacks = []
        self.watching = False
        self.timeout = None  # only meaningful for watch_once

        self._thread = None
        self._resp = None
        self._once = False

        self.key = key
        self.range_end = range_end
        self.start_revision = start_revision
        self.progress_notify = progress_notify
        self.prev_kv = prev_kv
        self.prefix = prefix
        self.all = all
        self.no_put = no_put
        self.no_delete = no_delete

    def set_default_timeout(self, timeout):
        """
        Set the default timeout of watch request

        :type timeout: int
        :param timeout: timeout in seconds
        """
        self.timeout = timeout

    def clear_revision(self):
        """
        Clear the start_revision that stored in watcher
        """
        self.start_revision = None
        self.revision = None

    def clear_callbacks(self):
        """
        Remove all callbacks
        """
        self.callbacks = []

    def request_create(self):
        """
        Start a watch request
        """
        if self.revision is not None:  # continue last watch
            self.start_revision = self.revision + 1
        return self.client.watch_create(
            key=self.key, range_end=self.range_end, start_revision=self.start_revision,
            progress_notify=self.progress_notify, prev_kv=self.prev_kv,
            prefix=self.prefix, all=self.all, no_put=self.no_put, no_delete=self.no_delete,
            timeout=self.timeout
        )

    def request_cancel(self):  # pragma: no cover
        """
        Cancel the watcher [Not Implemented because of etcd3 returns no watch_id]
        """
        # once really implemented, the error handling of Etcd3WatchCanceled when manually cancel should be considered
        if self.watch_id:
            # return self.client.watch_cancel(watch_id=self.watch_id)
            pass

    @staticmethod
    def get_filter(filter):
        """
        Get the event filter function

        :type filter: callable or regex string or EventType or None
        :param filter: will generate a filter function from this param
        :return: callable
        """
        if callable(filter):
            filter_func = filter
        elif isinstance(filter, (six.string_types, bytes)):
            regex = re.compile(filter)

            def filter_func(e):
                key = e.key
                if six.PY3:
                    try:
                        key = six.text_type(e.key, encoding='utf-8')
                    except Exception:
                        return
                return regex.match(key)
        elif filter is None:
            filter_func = lambda e: True
        elif isinstance(filter, EventType):
            filter_func = lambda e: e.type == filter
        else:
            raise TypeError('expect filter to be one of string, EventType, callable got %s' % type(filter))
        return filter_func

    def onEvent(self, filter_or_cb, cb=None):
        """
        Add a callback to a event that matches the filter

        If only one param is given, which is filter_or_cb, it will be treated as the callback.
        If any event comes, it will be called.

        :type filter_or_cb: callable or regex string or EventType
        :param filter_or_cb: filter or callback function
        :param cb: the callback function
        """
        if cb:
            filter = filter_or_cb
        else:
            filter = None
            cb = filter_or_cb
        if not callable(cb):
            raise TypeError('callback should be a callable')
        self.callbacks.append((self.get_filter(filter), filter, cb))

    def dispatch_event(self, event):
        """
        Find the callbacks, if callback's filter fits this event, call the callback

        :param event: Event
        """
        log.debug("dispatching event '%s'" % event)
        for filter, _, cb in self.callbacks:
            if filter(event):
                cb(event)

    def _ensure_callbacks(self):
        if not self.callbacks:
            raise TypeError("haven't watch on any event yet, use onEvent to watch a event")

    def _ensure_not_watching(self):
        if self.watching is True:
            raise RuntimeError("already watching")
        if self._thread and self._thread.is_alive() and self._thread.ident != get_ident():
            raise RuntimeError("watch thread seems running")

    def _kill_response_stream(self):
        if not self._resp or (self._resp and self._resp.raw.closed):
            return
        try:
            log.debug("closing response stream")
            self.request_cancel()
            s = socket.fromfd(self._resp.raw._fp.fileno(), socket.AF_INET, socket.SOCK_STREAM)
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            self._resp.raw.close()
            self._resp.close()
            self._resp.connection.close()
        except Exception:
            pass

    def run(self):
        """
        Run the watcher and handel events by callbacks
        """
        self._ensure_callbacks()
        self._ensure_not_watching()
        self.errors.clear()
        try:
            with self:
                for event in self:
                    self.dispatch_event(event)
        finally:
            self._kill_response_stream()
            self.watching = False

    def stop(self):
        """
        Stop watching, close the watch stream and exit the daemon thread
        """
        log.debug("stop watching")
        self.watching = False
        self._kill_response_stream()
        if self._thread and self._thread.is_alive() and self._thread.ident != get_ident():
            self._thread.join()

    cancel = stop

    def runDaemon(self):
        """
        Run Watcher in a daemon thread
        """
        self._ensure_callbacks()
        self._ensure_not_watching()
        t = self._thread = threading.Thread(target=self.run)
        t.setDaemon(True)
        t.start()

    def watch_once(self, filter=None, timeout=None):
        """
        watch the filtered event, once have event, return it
        if timed out, return None
        """
        filter = self.get_filter(filter)
        old_timeout = self.timeout
        self.timeout = timeout
        try:
            self._once = True
            with self:
                for event in self:
                    if filter(event):
                        return event
        except OnceTimeout:
            return
        finally:
            self.stop()
            self._once = False
            self.timeout = old_timeout

    def __enter__(self):
        self._ensure_not_watching()
        self._resp = self.request_create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __del__(self):
        self.stop()

    def __iter__(self):
        self.errors.clear()
        retries = 0
        while True:
            try:
                self.watching = True
                if log.level <= logging.DEBUG:
                    if self.all:
                        log.debug("start watching all keys")
                    elif self.prefix:
                        log.debug("start watching prefix '%s'" % self.key)
                    elif self.range_end:
                        log.debug("start watching from '%s' to '%s'" % (self.key, self.range_end))
                if not self._resp or self._resp.raw.closed:
                    self._resp = self.request_create()
                with self._resp as w:
                    event_stream = iter(w)
                    while self.watching:
                        if self._resp.raw._fp.fp is None:
                            raise ConnectionError("response connection closed")
                        r = next(event_stream)
                        log.debug("got a watch response")
                        self.revision = r.header.revision
                        if 'created' in r:
                            log.debug("watch request created")
                            self.start_revision = r.header.revision
                            self.watch_id = r.watch_id
                        if ('canceled' in r and r.canceled) or ('compact_revision' in r and r.compact_revision):
                            # etcd version < 3.3 returns compact_revision without canceled
                            compacted = False
                            if 'compact_revision' in r and r.compact_revision > 0:
                                compacted = True
                                err = Etcd3WatchCanceled("watch on compacted revision: %d" % self.start_revision, r)
                            else:
                                err = Etcd3WatchCanceled(r.cancel_reason, r)
                            if retries == 0 or retries >= self.max_retries:  # first request raise error to caller
                                raise err
                            else:
                                self.errors.append(err)
                                log.debug("failed watching (times:%d) retrying %s" % (retries, err))
                                if compacted:
                                    self.revision = r.compact_revision - 1  # next request start from compact_revision
                                self._kill_response_stream()  # close connection and throw Connection error
                        if 'events' in r:
                            for event in r.events:
                                yield Event(event, r.header)
            except (ConnectionError, ChunkedEncodingError) as e:
                # ConnectionError(MaxRetryError) means cannot reach the server
                if 'Max retries exceeded with url' in str(e):
                    raise  # no need to retry
                elif 'Read timed out.' in str(e) and self._once:  # if timed out and doing watch_once
                    raise OnceTimeout
                # ChunkedEncodingError usually means we lost the connection, could cause by watcher.stop()
                elif not self.watching:
                    # raise StopIteration  # watch stopped by user
                    return
                if retries < self.max_retries:  # connection unexpectedly or just reached the timeout
                    self.errors.append(e)
                    log.debug("failed watching (times:%d) retrying %s" % (retries, e))
                    retries += 1
                else:
                    # self.watching = False # no need the stop() always called in a with context
                    self.stop()
                    raise
            time.sleep(0.2)
