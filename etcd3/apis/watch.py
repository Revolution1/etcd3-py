from .base import BaseAPI
from ..models import WatchCreateRequestFilterType
from ..utils import check_param, incr_last_byte


class WatchAPI(BaseAPI):
    @check_param(at_least_one_of=['create_request', 'cancel_request'],
                 at_most_one_of=['create_request', 'cancel_request'])
    def watch(self, create_request=None, cancel_request=None):
        """
        PLEASE USE THE WATCH UTIL

        Watch watches for events happening or that have happened. Both input and output
        are streams; the input stream is for creating and canceling watchers and the output
        stream sends events. One watch RPC can watch on multiple key ranges, streaming events
        for several watches at once. The entire event history can be watched starting from the
        last compaction revision.

        :type create_request: dict
        :param create_request: None
        :type cancel_request: dict
        :param cancel_request: None
        """
        method = '/v3alpha/watch'
        data = {
            "create_request": create_request,
            "cancel_request": cancel_request
        }
        data = {k: v for k, v in data.items() if v is not None}
        return self.call_rpc(method, data=data, stream=True)

    @check_param(at_least_one_of=['key', 'all'], at_most_one_of=['range_end', 'prefix', 'all'])
    def watch_create(self, key, range_end=None, start_revision=None, progress_notify=None, filters=None, prev_kv=None,
                     prefix=False, all=False):
        """
        WatchCreate creates a watch stream on given key or key_range

        :type key: str
        :param key: key is the key to register for watching.
        :type range_end: str
        :param range_end: range_end is the end of the range [key, range_end) to watch. If range_end is not given,
            only the key argument is watched. If range_end is equal to '\0’, all keys greater than
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
        :type filters: list of WatchCreateRequestFilterType
        :param filters: filters filter the events at server side before it sends back to the watcher.
            default: [WatchCreateRequestFilterType.NOPUT]
        :type prev_kv: bool
        :param prev_kv: If prev_kv is set, created watcher gets the previous KV before the event happens.
            If the previous KV is already compacted, nothing will be returned.
        :type prefix: bool
        :param prefix: if the key is a prefix [default: False]
        :type all: bool
        :param all: all the keys [default: False]
        """
        if all:
            key = range_end = '\0'
        if prefix:
            range_end = incr_last_byte(key)
        filters = filters or [WatchCreateRequestFilterType.NOPUT]
        data = {
            "key": key,
            "range_end": range_end,
            "start_revision": start_revision,
            "progress_notify": progress_notify,
            "filters": filters,
            "prev_kv": prev_kv
        }
        data = {k: v for k, v in data.items() if v is not None}
        return self.watch(create_request=data)

    def watch_cancel(self, watch_id):
        """
        WatchCancel cancels a watch stream

        :type watch_id: int
        :param watch_id: watch_id is the watcher id to cancel so that no more events are transmitted.
        """
        data = {
            "watch_id": watch_id
        }
        return self.watch(cancel_request=data)
