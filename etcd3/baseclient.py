"""
synchronous client
"""

import abc
import os
import warnings

import semantic_version as sem
from six.moves import urllib_parse

from .apis import AuthAPI
from .apis import ClusterAPI
from .apis import ExtraAPI
from .apis import KVAPI
from .apis import LeaseAPI
from .apis import MaintenanceAPI
from .apis import WatchAPI
from .stateful import Lease
from .stateful import Lock
from .stateful import Txn
from .stateful import Watcher
from .swagger_helper import SwaggerSpec
from .utils import Etcd3Warning
from .version import __version__

rpc_swagger_json = os.path.join(os.path.dirname(__file__), 'rpc.swagger.json')

swaggerSpec = SwaggerSpec(rpc_swagger_json)  # TODO: swagger json may changed and need to implement multiple version


class BaseModelizedStreamResponse(object):  # pragma: no cover
    """
    Model of a stream response
    """

    @abc.abstractmethod
    def close(self):
        """
        close the stream
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError


class BaseClient(AuthAPI, ClusterAPI, KVAPI, LeaseAPI, MaintenanceAPI, WatchAPI, ExtraAPI):
    def __init__(self, host='localhost', port=2379, protocol='http',
                 cert=(), verify=None,
                 timeout=None, headers=None, user_agent=None, pool_size=30,
                 username=None, password=None, token=None):
        self.host = host
        self.port = port
        self.cert = None
        self.cert = cert
        self.protocol = protocol
        if cert:
            self.protocol = 'https'
        self.verify = verify or False
        self.user_agent = user_agent
        if not user_agent:
            self.user_agent = 'etcd3-py/' + __version__
        self.timeout = timeout
        self.headers = headers or {}
        self.username = username
        self.password = password
        self.token = token
        self.cluster_version = None
        self.server_version = None
        # TODO: /v3alpha will be deprecated an replaced by /v3 in v3.4
        # TODO: /v3beta will be deprecated in v3.5
        self.api_prefix = '/v3alpha'
        self._retrieve_version()

    def _retrieve_version(self):  # pragma: no cover
        try:
            import requests

            r = requests.get(self._url('/version'), cert=self.cert, verify=self.verify, timeout=0.3)  # 300ms will do
            r.raise_for_status()
            v = r.json()
            self.cluster_version = v["etcdcluster"]
            self.server_version = v["etcdserver"]
            if sem.Version(self.server_version) < sem.Version('3.2.2'):
                warnings.warn(Etcd3Warning("detected etcd server version(%s) is lower than 3.2.2, "
                                           "the gRPC-JSON-Gateway may not work" % self.server_version))
            if sem.Version(self.server_version) < sem.Version('3.3.0'):
                warnings.warn(Etcd3Warning("detected etcd server version(%s) is lower than 3.3.0, "
                                           "authentication methods may not work" % self.server_version))
            else:
                self.api_prefix = '/v3'
        except Exception:
            warnings.warn(Etcd3Warning("cannot detect etcd server version\n"
                                       "1. maybe is a network problem, please check your network connection\n"
                                       "2. maybe your etcd server version is too low, required: 3.2.2+"))

    @property
    def baseurl(self):
        """
        :return: baseurl from protocol, host, self
        """
        return '{}://{}:{}'.format(self.protocol, self.host, self.port)

    def _url(self, method):
        return urllib_parse.urljoin(self.baseurl, method)

    @staticmethod
    def _encodeRPCRequest(method, data):
        swpath = swaggerSpec.getPath(method)
        if not swpath:
            return data
        reqSchema = swpath.post.parameters[0].schema
        return reqSchema.encode(data)

    @staticmethod
    def _decodeRPCResponseData(method, data):
        swpath = swaggerSpec.getPath(method)
        if not swpath:
            return data
        reqSchema = swpath.post.responses._200.schema
        return reqSchema.decode(data)

    @classmethod
    def _modelizeResponseData(cls, method, data, decode=True):
        if len(data) == 1 and 'result' in data:
            data = data.get('result', {})  # the data of stream is put under the key: 'result'
        if decode:
            data = cls._decodeRPCResponseData(method, data)
        swpath = swaggerSpec.getPath(method)
        respModel = swpath.post.responses._200.schema.getModel()
        return respModel(data)

    @classmethod
    def _modelizeStreamResponse(cls, method, resp, decode=True):  # pragma: no cover
        raise NotImplemented

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):  # pragma: no cover
        """
        close all connections in connection pool
        """
        raise NotImplementedError

    def _get(self, url, **kwargs):  # pragma: no cover
        r"""
        Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        raise NotImplementedError

    def _post(self, url, data=None, json=None, **kwargs):  # pragma: no cover
        r"""
        Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        raise NotImplementedError

    def call_rpc(self, method, data=None, stream=False, encode=True, raw=False, **kwargs):  # pragma: no cover
        """
        call ETCDv3 RPC and return response object

        :type method: str
        :param method: the rpc method, which is a path of RESTful API
        :type data: dict
        :param data: request payload to be post to ETCD's gRPC-JSON-Gateway default: {}
        :type stream: bool
        :param stream: whether return a stream response object, default: False
        :type encode: bool
        :param encode: whether encode the data before post, default: True
        :param kwargs: additional params to pass to the http request, like headers, timeout etc.
        :return: Etcd3RPCResponseModel or Etcd3StreamingResponse
        """
        raise NotImplementedError

    def auth(self, username=None, password=None):  # pragma: no cover
        """
        call auth.authenticate and save the token

        :type username: str
        :param username: username
        :type password: str
        :param password: password
        """
        pass

    def Txn(self):
        """
        Initialize a Transaction
        """
        return Txn(self)

    def Lease(self, ttl, ID=0, new=True):
        """
        Initialize a Lease

        :type ID: int
        :param ID: ID is the requested ID for the lease. If ID is set to 0, the lessor chooses an ID.
        :type new: bool
        :param new: whether grant a new lease or maintain a exist lease by its id [default: True]
        """
        return Lease(self, ttl=ttl, ID=ID, new=new)

    def Watcher(self, key=None, range_end=None, max_retries=-1, start_revision=None, progress_notify=None,
                prev_kv=None, prefix=None, all=None, no_put=False, no_delete=False):
        """
        Initialize a Watcher

        :type key: str
        :param key: key is the key to register for watching.
        :type range_end: str
        :param range_end: range_end is the end of the range [key, range_end) to watch. If range_end is not given,
            only the key argument is watched. If range_end is equal to '\0', all keys greater than
            or equal to the key argument are watched.
            If the range_end is one bit larger than the given key,
            then all keys with the prefix (the given key) will be watched.
        :type max_retries: int
        :param max_retries: max retries when watch failed due to network problem, -1 means no limit [default: -1]
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
        :return: Watcher
        """
        return Watcher(client=self, key=key, range_end=range_end, max_retries=max_retries,
                       start_revision=start_revision,
                       progress_notify=progress_notify, prev_kv=prev_kv, prefix=prefix, all=all, no_put=no_put,
                       no_delete=no_delete)

    def Lock(self, lock_name, lock_ttl=Lock.DEFAULT_LOCK_TTL, reentrant=None, lock_prefix='_locks'):
        return Lock(self, lock_name=lock_name, lock_ttl=lock_ttl, reentrant=reentrant, lock_prefix=lock_prefix)
