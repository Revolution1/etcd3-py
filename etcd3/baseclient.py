"""
synchronous client
"""

import abc
import os

from six.moves import urllib_parse

from .apis import AuthAPI
from .apis import ClusterAPI
from .apis import ExtraAPI
from .apis import KVAPI
from .apis import LeaseAPI
from .apis import MaintenanceAPI
from .apis import WatchAPI
from .swagger_helper import SwaggerSpec
from .version import __version__

rpc_swagger_json = os.path.join(os.path.dirname(__file__), 'rpc.swagger.json')

swaggerSpec = SwaggerSpec(rpc_swagger_json)


class BaseModelizedStreamResponse(object):
    """
    Model of a stream response
    """

    @abc.abstractmethod
    def close(self):
        """
        close the stream
        """
        raise NotImplemented

    @abc.abstractmethod
    def __iter__(self):
        raise NotImplemented


class BaseClient(AuthAPI, ClusterAPI, KVAPI, LeaseAPI, MaintenanceAPI, WatchAPI, ExtraAPI):
    def __init__(self, host='localhost', port=2379, protocol='http',
                 ca_cert=None, cert_key=None, cert_cert=None,
                 timeout=None, headers=None, user_agent=None, pool_size=30,
                 username=None, password=None, token=None):
        self.host = host
        self.port = port
        self.cert = None
        self.ca_cert = ca_cert
        self.cert_key = cert_key
        self.cert_cert = cert_cert
        if ca_cert or cert_key and cert_cert:
            self.protocol = 'https'
        if ca_cert:
            self.cert = ca_cert
        if cert_cert and cert_key:
            self.cert = (cert_cert, cert_key)
        self.user_agent = user_agent
        if not user_agent:
            self.user_agent = 'etcd3-py/' + __version__
        self.protocol = protocol
        self.timeout = timeout
        self.headers = headers or {}
        self.username = username
        self.password = password
        self.token = token

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
    def _modelizeStreamResponse(cls, method, resp, decode=True):
        raise NotImplemented

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """
        close all connections in connection pool
        """
        raise NotImplemented

    def _get(self, url, **kwargs):
        r"""
        Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        raise NotImplemented

    def _post(self, url, data=None, json=None, **kwargs):
        r"""
        Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        raise NotImplemented

    def call_rpc(self, method, data=None, stream=False, encode=True, raw=False, **kwargs):
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
        raise NotImplemented

    def auth(self, username=None, password=None):
        """
        call auth.authenticate and save the token

        :type username: str
        :param username: username
        :type password: str
        :param password: password
        """
        pass
