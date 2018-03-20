import logging
import re
import socket
import threading
import time

import six
from requests import ConnectionError
from requests.exceptions import ChunkedEncodingError

from ..models import EventEventType
from ..utils import check_param

log = logging.getLogger('etcd3.Watch')
EventType = EventEventType


class ManualStopped(Exception):
    pass


class KeyValue(object):  # pragma: no cover
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
    def __init__(self, data):
        super(Event, self).__init__(data.kv._data)
        self.type = getattr(data, 'type', EventType.PUT)  # default is PUT
        self._data['type'] = self.type
        self.prev_kv = None
        if 'prev_kv' in data:
            self.prev_kv = KeyValue(data.prev_kv._data)
        self._data['prev_kv'] = self.prev_kv

    def __repr__(self):
        return "<WatchEvent '%s'>" % self.key


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
        :type key: str
        :param key: key is the key to register for watching.
        :type range_end: str
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
        self.retries = 0
        self.errors = []
        if max_retries == -1:
            max_retries = 9223372036854775807  # maxint
        self.max_retries = max_retries
        self.callbacks = []
        self.watching = False

        self._thread = None
        self._resp = None

        self.key = key
        self.range_end = range_end
        self.start_revision = start_revision
        self.progress_notify = progress_notify
        self.prev_kv = prev_kv
        self.prefix = prefix
        self.all = all
        self.no_put = no_put
        self.no_delete = no_delete

    def request_create(self):
        if self.revision is not None:  # continue last watch
            self.start_revision = self.revision + 1
        return self.client.watch_create(
            key=self.key, range_end=self.range_end, start_revision=self.start_revision,
            progress_notify=self.progress_notify, prev_kv=self.prev_kv,
            prefix=self.prefix, all=self.all, no_put=self.no_put, no_delete=self.no_delete
        )

    def request_cancel(self):  # pragma: no cover
        pass

    def onEvent(self, match_or_cb, cb=None):
        if cb:
            match = match_or_cb
        else:
            match = None
            cb = match_or_cb
        if not callable(cb):
            raise TypeError('callback should be a callable')
        if callable(match):
            match_func = match
        elif isinstance(match, (six.string_types, bytes)):
            regex = re.compile(match)

            def match_func(e):
                key = e.key
                if six.PY3:
                    try:
                        key = six.text_type(e.key, encoding='utf-8')
                    except Exception:
                        return
                return regex.match(key)
        elif match is None:
            match_func = lambda e: True
        elif isinstance(match, EventType):
            match_func = lambda e: e.type == match
        else:
            raise TypeError('expect match to be one of string, EventType, callable got %s' % type(match))
        self.callbacks.append((match_func, match, cb))

    def clear_callbacks(self):
        self.callbacks = []

    def dispatch_event(self, event):
        log.debug("dispatching event '%s'" % event)
        for match_func, match, cb in self.callbacks:
            if match_func(event):
                cb(event)

    def _run(self):
        log.debug("start watching '%s'" % self.key)
        with self.request_create() as w:
            self._resp = w.resp
            resp = iter(w)
            while self.watching:
                r = next(resp)
                log.debug("got a watch response")
                self.revision = r.header.revision
                if 'created' in r:
                    log.debug("watch request created")
                    self.start_revision = r.header.revision
                if 'events' in r:
                    for event in r.events:
                        self.dispatch_event(Event(event))
        self.watching = False

    def stop(self):
        if self.watching == False:
            raise RuntimeError("not watching")
        log.debug("watching stopping")
        self.watching = False
        try:
            # if six.PY2:
            #     self._resp.raw._fp.close()
            # else:
            # self._resp.raw._connection.close()
            # self._resp.raw._fp.close()
            s = socket.fromfd(self._resp.raw._fp.fileno(), socket.AF_INET, socket.SOCK_STREAM)
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except Exception:
            self._resp.connection.close()

    cancel = stop

    def run(self):
        if self.watching == True:
            raise RuntimeError("already watching")
        self.errors = []
        retries = 0
        try:
            while True:
                try:
                    self.watching = True
                    self._run()
                    break
                except (ConnectionError, ChunkedEncodingError) as e:
                    if not self.watching:
                        break
                    if retries < self.max_retries:
                        self.errors.append(e)
                        log.debug("failed watching (times:%d) retrying %s" % (retries, e))
                        retries += 1
                    else:
                        self.watching = False
                        raise
                time.sleep(0.3)
        finally:
            self.watching = False

    def runDaemon(self):
        if self.watching == True:
            raise RuntimeError("already watching")
        t = self._thread = threading.Thread(target=self.run)
        t.setDaemon(True)
        t.start()

    def __enter__(self):
        if self.watching == True:
            raise RuntimeError("already watching")
        self._resp = self.request_create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __iter__(self):
        self.errors = []
        retries = 0
        while True:
            try:
                if self.watching == True:
                    raise RuntimeError("already watching")
                self.watching = True
                log.debug("start watching '%s'" % self.key)
                with self.request_create() as w:
                    self._resp = w.resp
                    resp = iter(w)
                    while self.watching:
                        r = next(resp)
                        log.debug("got a watch response")
                        self.revision = r.header.revision
                        if 'created' in r:
                            log.debug("watch request created")
                            self.start_revision = r.header.revision
                        if 'events' in r:
                            for event in r.events:
                                yield Event(event)
            # same as self.run()
            except (ConnectionError, ChunkedEncodingError) as e:  # pragma: no cover
                if not self.watching:
                    break
                if retries < self.max_retries:
                    self.errors.append(e)
                    log.debug("failed watching (times:%d) retrying %s" % (retries, e))
                    retries += 1
                else:
                    raise
            time.sleep(0.3)
