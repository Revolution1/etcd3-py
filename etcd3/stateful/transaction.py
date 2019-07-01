import copy

import six

from ..apis import KVAPI
from ..models import CompareCompareResult
from ..models import CompareCompareTarget
from ..models import RangeRequestSortOrder
from ..models import RangeRequestSortTarget
from ..utils import check_param
from ..utils import enum_value
from ..utils import incr_last_byte

kv = KVAPI()


class Txn(object):
    """
    Txn (transaction) util provides a human friendly way to build kv.txn request
    Usage:

    >>> from etcd3 import Client, Txn
    >>> txn = Txn(Client())
    >>> txn.compare(txn.key('foo').value == 'bar')
    >>> txn.success(txn.put('foo', 'bra'))
    >>> txn.commit()
    etcdserverpbTxnResponse(header=etcdserverpbResponseHeader(cluster_id=11588568905070377092, member_id=128088275939295631, revision=15656, raft_term=4), succeeded=True, responses=[etcdserverpbResponseOp(response_put=etcdserverpbPutResponse(header=etcdserverpbResponseHeader(revision=15656)))])


    From google paxosdb paper:

    Our implementation hinges around a powerful primitive which we call MultiOp. All other database
    operations except for iteration are implemented as a single call to MultiOp. A MultiOp is applied atomically
    and consists of three components:

    1.  A list of tests called guard. Each test in guard checks a single entry in the database. It may check
        for the absence or presence of a value, or compare with a given value. Two different tests in the guard
        may apply to the same or different entries in the database. All tests in the guard are applied and
        MultiOp returns the results. If all tests are true, MultiOp executes t op (see item 2 below), otherwise
        it executes f op (see item 3 below).

    2.  A list of database operations called t op. Each operation in the list is either an insert, delete, or
        lookup operation, and applies to a single database entry. Two different operations in the list may apply
        to the same or different entries in the database. These operations are executed if guard evaluates to true.

    3.  A list of database operations called f op. Like t op, but executed if guard evaluates to false.
    """

    def __init__(self, client, compare=None, success=None, failure=None):
        """
        :type client: BaseClient
        :param client: the instance of etcd3's client
        :param compare: guard components of the transaction, default to []
        :param success: success components of the transaction, default to []
        :param failure: failure components of the transaction, default to []
        """
        self.client = client
        self._compare = list(compare or [])
        self._success = list(success or [])
        self._failure = list(failure or [])
        self._committed = False

    def clear(self):  # pragma: no cover
        """
        clear all ops
        """
        self._compare = []
        self._success = []
        self._failure = []

    def compare(self, compareOp):
        """
        Add a test to the transaction guard component

        :param compareOp: TxnCompareOp
        :return: self
        """
        if isinstance(compareOp, TxnCompareOp):
            compareOp = compareOp.to_compare()
        self._compare.append(compareOp)
        return self

    If = compare

    def success(self, successOp):
        """
        Add a database operation to the transaction success component
        """
        self._success.append(successOp)
        return self

    Then = success

    def failure(self, failureOp):
        """
        Add a database operation to the transaction failure component
        """
        self._failure.append(failureOp)
        return self

    Else = failure

    def commit(self):
        return self.client.txn(compare=self._compare, success=self._success, failure=self._failure)

    @staticmethod
    @check_param(at_least_one_of=['key', 'all'], at_most_one_of=['range_end', 'prefix', 'all'])
    def key(key=None, range_end=None, prefix=None, all=None):
        """
        Get the TxnCompareOp of a key

        :type key: str or bytes
        :param key: key is the subject key for the comparison operation.
        :type range_end: str or bytes
        :param range_end: range_end is the upper bound on the requested range [key, range_end).
            If range_end is '\0', the range is all keys >= key.
            If range_end is key plus one (e.g., "aa"+1 == "ab", "a\xff"+1 == "b"),
            then the range request gets all keys prefixed with key.
            If both key and range_end are '\0', then the range request returns all keys.
        :type prefix: bool
        :param prefix: if the key is a prefix [default: False]
        :type all: bool
        :param all: all the keys [default: False]
        :return: TxnCompareOp
        """
        if all:
            key = range_end = '\0'
        if prefix:
            range_end = incr_last_byte(key)
        return TxnCompareOp(key, range_end=range_end)

    @staticmethod
    def range(
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
        prefix=None,
        all=None,
    ):
        """
        Operation of keys in the range from the key-value store.

        :type key: str or bytes
        :param key: key is the first key for the range. If range_end is not given, the request only looks up key.
        :type range_end: str or bytes
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
        """
        return kv.range(
            key=key,
            range_end=range_end,
            limit=limit,
            revision=revision,
            serializable=serializable,
            keys_only=keys_only,
            count_only=count_only,
            min_mod_revision=min_mod_revision,
            max_mod_revision=max_mod_revision,
            min_create_revision=min_create_revision,
            max_create_revision=max_create_revision,
            sort_order=sort_order,
            sort_target=sort_target,
            prefix=prefix,
            all=all,
            txn_obj=True
        )

    @staticmethod
    def put(key, value, lease=0, prev_kv=False, ignore_value=False, ignore_lease=False):
        """
        Operation of puts the given key into the key-value store.
        A put request increments the revision of the key-value store
        and generates one event in the event history.

        :type key: str or bytes
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
        """
        return kv.put(key=key, value=value, lease=lease, prev_kv=prev_kv, ignore_value=ignore_value,
                      ignore_lease=ignore_lease, txn_obj=True)

    @staticmethod
    def delete(key=None, range_end=None, prev_kv=False, prefix=None, all=None):
        """
        Operation of deletes the given range from the key-value store.
        A delete request increments the revision of the key-value store
        and generates a delete event in the event history for every deleted key.

        :type key: str or bytes
        :param key: key is the first key to delete in the range.
        :type range_end: str or bytes
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
        """
        return kv.delete_range(key=key, range_end=range_end, prev_kv=prev_kv, prefix=prefix, all=all, txn_obj=True)

    def __copy__(self):
        return Txn(
            client=self.client,
            compare=self._compare[:],
            success=self._success[:],
            failure=self._failure[:]
        )

    def clone(self):
        """
        :return: Txn
        """
        return self.__copy__()


class TxnCompareOp(object):
    """
    The operator of transaction's compare part
    """

    def __init__(self, key, range_end=None):
        """
        :param key: the key to compare
        """
        if not isinstance(key, (six.string_types, bytes)):
            raise TypeError("parameter 'key' expects (str, bytes) got '%s'" % type(key))
        self._key = key
        self._range_end = range_end
        self._result = None
        self._target = None
        self._tmp_target = None
        self._version = None
        self._create_revision = None
        self._mod_revision = None
        self._lease = None
        self._value = None

    def __check_target(self):
        if self._target:
            raise TypeError("already set a target '%s'" % enum_value(self._target))

    @property
    def value(self):
        """
        represents the value of the key
        """
        self.__check_target()
        self._tmp_target = CompareCompareTarget.VALUE
        return self

    @property
    def mod(self):
        """
        represents the mod_revision of the key
        """
        self.__check_target()
        self._tmp_target = CompareCompareTarget.MOD
        return self

    @property
    def version(self):
        """
        represents the version of the key
        """
        self.__check_target()
        self._tmp_target = CompareCompareTarget.VERSION
        return self

    @property
    def create(self):
        """
        represents the create_revision of the key
        """
        self.__check_target()
        self._tmp_target = CompareCompareTarget.CREATE
        return self

    @property
    def lease(self):
        """
        represents the lease_id of the key

        ref: https://github.com/etcd-io/etcd/blob/v3.3.12/clientv3/compare.go#L87-L91
            LeaseValue compares a key's LeaseID to a value of your choosing. The empty
            LeaseID is 0, otherwise known as `NoLease`.
        """
        self.__check_target()
        self._tmp_target = CompareCompareTarget.LEASE
        return self

    def __set_target(self, v):
        self._target = self._tmp_target
        if not self._target:
            raise TypeError(
                "should specify a target (version, create, mod, value) to compare, "
                "e.g. txn.key('foo').value == 'bar'"
            )
        if enum_value(self._target) == CompareCompareTarget.VALUE.value:
            if not isinstance(v, (six.string_types, bytes)):
                raise TypeError("expect (str, bytes) got '%s'" % type(v))
            self._value = v
        elif enum_value(self._target) == CompareCompareTarget.VERSION.value:
            if not isinstance(v, int):
                raise TypeError("expect int got '%s'" % type(v))
            self._version = v
        elif enum_value(self._target) == CompareCompareTarget.MOD.value:
            if not isinstance(v, int):
                raise TypeError("expect int got '%s'" % type(v))
            self._mod_revision = v
        elif enum_value(self._target) == CompareCompareTarget.CREATE.value:
            if not isinstance(v, int):
                raise TypeError("expect int got '%s'" % type(v))
            self._create_revision = v
        elif enum_value(self._target) == CompareCompareTarget.LEASE.value:
            if not isinstance(v, int):
                raise TypeError("expect int got '%s'" % type(v))
            self._lease = v

    def __eq__(self, other):
        obj = copy.copy(self)
        obj.__set_target(other)
        obj._result = CompareCompareResult.EQUAL
        return obj

    def __gt__(self, other):
        obj = copy.copy(self)
        obj.__set_target(other)
        obj._result = CompareCompareResult.GREATER
        return obj

    def __lt__(self, other):
        obj = copy.copy(self)
        obj.__set_target(other)
        obj._result = CompareCompareResult.LESS
        return obj

    def __ne__(self, other):
        obj = copy.copy(self)
        obj.__set_target(other)
        obj._result = CompareCompareResult.NOT_EQUAL
        return obj

    def __ge__(self, other):
        raise NotImplementedError

    def __le__(self, other):
        raise NotImplementedError

    def to_compare(self):
        """
        return the compare payload that the rpc accepts
        """
        data = {
            "result": enum_value(self._result),
            "target": enum_value(self._target),
            "key": self._key,
            "range_end": self._range_end,
            "version": self._version,
            "create_revision": self._create_revision,
            "mod_revision": self._mod_revision,
            "lease": self._lease,
            "value": self._value
        }
        return {k: v for k, v in data.items() if v is not None}
