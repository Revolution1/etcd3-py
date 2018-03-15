from .base import BaseAPI
from ..models import RangeRequestSortOrder
from ..models import RangeRequestSortTarget
from ..utils import check_param
from ..utils import incr_last_byte


class KVAPI(BaseAPI):
    def compact(self, revision, physical=False):
        """
        Compact compacts the event history in the etcd key-value store. The key-value
        store should be periodically compacted or the event history will continue to grow
        indefinitely.

        :type revision: int
        :param revision: revision is the key-value store revision for the compaction operation.
        :type physical: bool
        :param physical: physical is set so the RPC will wait until the compaction is physically
            applied to the local database such that compacted entries are totally
            removed from the backend database. [default: False]
        """
        method = '/v3alpha/kv/compaction'
        data = {
            "revision": revision,
            "physical": physical
        }
        return self.call_rpc(method, data=data)

    @check_param(at_least_one_of=['key', 'all'], at_most_one_of=['range_end', 'prefix', 'all'])
    def delete_range(self, key=None, range_end=None, prev_kv=False, prefix=False, all=False, txn_obj=False):
        """
        DeleteRange deletes the given range from the key-value store.
        A delete request increments the revision of the key-value store
        and generates a delete event in the event history for every deleted key.

        :type key: str
        :param key: key is the first key to delete in the range.
        :type range_end: str
        :param range_end: range_end is the key following the last key to delete for the range [key, range_end).
            If range_end is not given, the range is defined to contain only the key argument.
            If range_end is one bit larger than the given key, then the range is all the keys
            with the prefix (the given key).
            If range_end is '\0', the range is all keys greater than or equal to the key argument.
        :type prev_kv: bool
        :param prev_kv: If prev_kv is set, etcd gets the previous key-value pairs before deleting it.
            The previous key-value pairs will be returned in the delete response.
        :type prefix: bool
        :param prefix: if the key is a prefix [default: False]
        :type all: bool
        :param all: all the keys [default: False]
        :type txn_obj: bool
        :param txn_obj: return dict for the txn instead of call the api
        """
        method = '/v3alpha/kv/deleterange'
        if all:
            key = range_end = '\0'
        if prefix:
            range_end = incr_last_byte(key)
        data = {
            "key": key,
            "range_end": range_end,
            "prev_kv": prev_kv
        }
        data = {k: v for k, v in data.items() if v is not None}
        if txn_obj:
            return {"request_delete_range": data}
        return self.call_rpc(method, data=data)

    def put(self, key, value, lease=0, prev_kv=False, ignore_value=False, ignore_lease=False, txn_obj=False):
        """
        Put puts the given key into the key-value store.
        A put request increments the revision of the key-value store
        and generates one event in the event history.

        :type key: str
        :param key: key is the key, in bytes, to put into the key-value store.
        :type value: str
        :param value: value is the value, in bytes, to associate with the key in the key-value store.
        :type lease: int
        :param lease: lease is the lease ID to associate with the key in the key-value store. A lease
            value of 0 indicates no lease.
        :type prev_kv: bool
        :param prev_kv: If prev_kv is set, etcd gets the previous key-value pair before changing it.
            The previous key-value pair will be returned in the put response.
        :type ignore_value: bool
        :param ignore_value: If ignore_value is set, etcd updates the key using its current value.
            Returns an error if the key does not exist.
        :type ignore_lease: bool
        :param ignore_lease: If ignore_lease is set, etcd updates the key using its current lease.
            Returns an error if the key does not exist.
        :type txn_obj: bool
        :param txn_obj: return dict for the txn instead of call the api
        """
        method = '/v3alpha/kv/put'
        data = {
            "key": key,
            "value": value,
            "lease": lease,
            "prev_kv": prev_kv,
            "ignore_value": ignore_value,
            "ignore_lease": ignore_lease
        }
        data = {k: v for k, v in data.items() if v is not None}
        if txn_obj:
            return {"request_put": data}
        return self.call_rpc(method, data=data)

    @check_param(at_least_one_of=['key', 'all'], at_most_one_of=['range_end', 'prefix', 'all'])
    def range(
        self,
        key=None,
        range_end=None,
        limit=0,
        revision=None,
        serializable=False,
        keys_only=False,
        count_only=False,
        min_mod_revision=None,
        max_mod_revision=None,
        min_create_revision=None,
        max_create_revision=None,
        sort_order=RangeRequestSortOrder.NONE,
        sort_target=RangeRequestSortTarget.KEY,
        prefix=False,
        all=False,
        txn_obj=False
    ):
        """
        Range gets the keys in the range from the key-value store.

        :type key: str
        :param key: key is the first key for the range. If range_end is not given, the request only looks up key.
        :type range_end: str
        :param range_end: range_end is the upper bound on the requested range [key, range_end).
            If range_end is '\0', the range is all keys >= key.
            If range_end is key plus one (e.g., "aa"+1 == "ab", "a\xff"+1 == "b"),
            then the range request gets all keys prefixed with key.
            If both key and range_end are '\0', then the range request returns all keys.
        :type limit: int
        :param limit: limit is a limit on the number of keys returned for the request. When limit is set to 0,
            it is treated as no limit.
        :type revision: int
        :param revision: revision is the point-in-time of the key-value store to use for the range.
            If revision is less or equal to zero, the range is over the newest key-value store.
            If the revision has been compacted, ErrCompacted is returned as a response.
        :type sort_order: RangeRequestSortOrder
        :param sort_order: sort_order is the order for returned sorted results.
        :type sort_target: RangeRequestSortTarget
        :param sort_target: sort_target is the key-value field to use for sorting.
        :type serializable: bool
        :param serializable: serializable sets the range request to use serializable member-local reads.
            Range requests are linearizable by default; linearizable requests have higher
            latency and lower throughput than serializable requests but reflect the current
            consensus of the cluster. For better performance, in exchange for possible stale reads,
            a serializable range request is served locally without needing to reach consensus
            with other nodes in the cluster.
        :type keys_only: bool
        :param keys_only: keys_only when set returns only the keys and not the values.
        :type count_only: bool
        :param count_only: count_only when set returns only the count of the keys in the range.
        :type min_mod_revision: int
        :param min_mod_revision: min_mod_revision is the lower bound for returned key mod revisions; all keys with
            lesser mod revisions will be filtered away.
        :type max_mod_revision: int
        :param max_mod_revision: max_mod_revision is the upper bound for returned key mod revisions; all keys with
            greater mod revisions will be filtered away.
        :type min_create_revision: int
        :param min_create_revision: min_create_revision is the lower bound for returned key create revisions; all keys with
            lesser create revisions will be filtered away.
        :type max_create_revision: int
        :param max_create_revision: max_create_revision is the upper bound for returned key create revisions; all keys with
            greater create revisions will be filtered away.
        :type prefix: bool
        :param prefix: if the key is a prefix [default: False]
        :type all: bool
        :param all: all the keys [default: False]
        :type txn_obj: bool
        :param txn_obj: return dict for the txn instead of call the api
        """
        method = '/v3alpha/kv/range'
        if all:
            key = range_end = '\0'
        if prefix:
            range_end = incr_last_byte(key)
        data = {
            "key": key,
            "range_end": range_end,
            "limit": limit,
            "revision": revision,
            "sort_order": sort_order,
            "sort_target": sort_target,
            "serializable": serializable,
            "keys_only": keys_only,
            "count_only": count_only,
            "min_mod_revision": min_mod_revision,
            "max_mod_revision": max_mod_revision,
            "min_create_revision": min_create_revision,
            "max_create_revision": max_create_revision
        }
        data = {k: v for k, v in data.items() if v is not None}
        if txn_obj:
            return {"request_range": data}
        return self.call_rpc(method, data=data)

    def txn(self, compare, success, failure):
        """
        Txn processes multiple requests in a single transaction.
        A txn request increments the revision of the key-value store
        and generates events with the same revision for every completed request.
        It is not allowed to modify the same key several times within one txn.

        :type compare: list of dict
        :param compare: compare is a list of predicates representing a conjunction of terms.
            If the comparisons succeed, then the success requests will be processed in order,
            and the response will contain their respective responses in order.
            If the comparisons fail, then the failure requests will be processed in order,
            and the response will contain their respective responses in order.
        :type success: list of dict
        :param success: success is a list of requests which will be applied when compare evaluates to true.
        :type failure: list of dict
        :param failure: failure is a list of requests which will be applied when compare evaluates to false.
        """
        method = '/v3alpha/kv/txn'
        data = {
            "compare": compare,
            "success": success,
            "failure": failure
        }
        return self.call_rpc(method, data=data)
