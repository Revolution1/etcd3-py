"""
asynchronous client
"""

import json
import ssl
import warnings

import aiohttp
import six
from aiohttp.client import _RequestContextManager

from .baseclient import BaseClient
from .baseclient import BaseModelizedStreamResponse
from .baseclient import DEFAULT_VERSION
from .errors import Etcd3Exception
from .errors import Etcd3StreamError
from .errors import get_client_error
from .utils import iter_json_string, Etcd3Warning


class ModelizedResponse(object):
    def __init__(self, client, method, resp, decode=True):
        self.client = client
        self._coro = resp
        self._method = method
        self._resp = None
        self._decode = decode

    async def __modelize(self):
        self._resp = await self._coro
        await self.client._raise_for_status(self._resp)
        data = await self._resp.json()
        return self.client._modelizeResponseData(self._method, data, self._decode)

    def __await__(self):
        return self.__modelize().__await__()


class ModelizedStreamResponse(BaseModelizedStreamResponse):
    """
    Model of a stream response
    """

    def __init__(self, client, method, resp, decode=True):
        """
        :param resp: aiohttp.ClientResponse
        """
        self.client = client
        self.resp = resp
        self.decode = decode
        self.method = method

    @property
    def connection(self):
        return self.resp.connection

    @property
    def resp_iter(self):
        return ResponseIter(self.resp)

    def close(self):
        """
        close the stream
        """
        return self.resp.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # def __del__(self):
    #     self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if isinstance(self.resp, _RequestContextManager):
            self.resp = await self.resp
            await self.client._raise_for_status(self.resp)
        data = await self.resp_iter.next()
        data = json.loads(str(data, encoding='utf-8'))
        if data.get('error'):  # pragma: no cover
            # {"error":{"grpc_code":14,"http_code":503,"message":"rpc error: code = Unavailable desc = transport is closing","http_status":"Service Unavailable"}}
            err = data.get('error')
            raise get_client_error(err.get('message'), code=err.get('code'), status=err.get('http_code'))
        r = self.client._modelizeResponseData(self.method, data, decode=self.decode)
        if r.result:
            r = r.result
        return r


class ResponseIter(object):
    """
    yield response content by every json object
    we don't yield by line, because the content of etcd's gRPC-JSON-Gateway stream response
    does not have a delimiter between each object by default. (only one line)

    https://github.com/grpc-ecosystem/grpc-gateway/pull/497/files

    :param resp: aiohttp.ClientResponse
    :return: dict
    """

    def __init__(self, resp):
        self.resp = resp
        self.buf = []
        self.bracket_flag = 0
        self.left_chunk = b''
        self.i = 0

    def __aiter__(self):
        return self

    async def next(self):
        while True:
            chunk = self.left_chunk
            for ok, s, i in iter_json_string(chunk, start=self.i, resp=self.resp, err_cls=Etcd3StreamError):
                if ok:
                    self.i = i
                    return s
                else:
                    self.i = 0
                    self.left_chunk += await self.resp.content.readany()
                    if not self.left_chunk:  # pragma: no cover
                        if self.buf:
                            raise Etcd3StreamError("Stream decode error", self.buf, self.resp)
                        raise StopAsyncIteration

    __anext__ = next


class AioClient(BaseClient):
    def __init__(self, host='127.0.0.1', port=2379, protocol='http',
                 cert=(), verify=None,
                 timeout=None, headers=None, user_agent=None, pool_size=30,
                 username=None, password=None, token=None,
                 server_version=DEFAULT_VERSION, cluster_version=DEFAULT_VERSION):
        super(AioClient, self).__init__(host=host, port=port, protocol=protocol,
                                        cert=cert, verify=verify,
                                        timeout=timeout, headers=headers, user_agent=user_agent, pool_size=pool_size,
                                        username=username, password=password, token=token,
                                        server_version=server_version, cluster_version=cluster_version)
        self.ssl_context = None
        if self.cert:
            if verify is False:
                cert_reqs = ssl.CERT_NONE
                cafile = None
            elif verify is True:
                cert_reqs = ssl.CERT_REQUIRED
                import certifi
                cafile = certifi.where()
            elif isinstance(verify, six.string_types):
                cert_reqs = ssl.CERT_REQUIRED
                cafile = verify
            else:
                raise TypeError("verify must be bool or string of the ca file path")
            # the ssl problem is a pain in the ass, seems i can never get it right
            # https://github.com/requests/requests/issues/1847
            # https://stackoverflow.com/questions/44316292/ssl-sslerror-tlsv1-alert-protocol-version
            self.ssl_context = ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)
            if not hasattr(ssl, 'PROTOCOL_TLSv1_1'):  # should support TLSv1.2 to pass the test
                warnings.warn(Etcd3Warning("the openssl version of your python is too old to support TLSv1.1+,"
                                           "please upgrade you python"))
            ssl_context.verify_mode = cert_reqs
            ssl_context.load_verify_locations(cafile=cafile)
            ssl_context.load_cert_chain(*self.cert)
        connector = aiohttp.TCPConnector(limit=pool_size, ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)

    async def close(self):
        """
        close all connections in connection pool
        """
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _modelizeResponse(self, method, resp, decode=True):
        return ModelizedResponse(self, method, resp, decode)

    def _modelizeStreamResponse(self, method, resp, decode=True):
        return ModelizedStreamResponse(self, method, resp, decode)

    def _get(self, url, **kwargs):
        r"""
        Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: aiohttp.ClientResponse
        """
        return self.session.get(url, **kwargs)

    def _post(self, url, data=None, json=None, **kwargs):
        r"""
        Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: aiohttp.ClientResponse
        """
        return self.session.post(url, data=data, json=json, **kwargs)

    @staticmethod
    async def _raise_for_status(resp):
        status = resp.status
        if status < 400:
            return
        try:
            data = await resp.json()
        except Exception:
            error = resp._content or resp.reason
            code = 2
        else:
            error = data.get('error')
            code = data.get('code')
        raise get_client_error(error, code, status, resp)

    def call_rpc(self, method, data=None, stream=False, encode=True, raw=False, **kwargs):
        """
        call ETCDv3 RPC and return response object

        :type method: str
        :param method: the rpc method, which is a path of RESTful API
        :type data: dict or str
        :param data: request payload to be post to ETCD's gRPC-JSON-Gateway default: {}
        :type stream: bool
        :param stream: whether return a stream response object, default: False
        :type encode: bool
        :param encode: whether encode the data before post, default: True
        :param kwargs: additional params to pass to the http request, like headers, timeout etc.
        :return: Etcd3RPCResponseModel or Etcd3StreamingResponse
        """
        data = data or {}
        kwargs.setdefault('timeout', self.timeout)
        if self.token:
            kwargs.setdefault('headers', {}).setdefault('authorization', self.token)
        kwargs.setdefault('headers', {}).setdefault('user_agent', self.user_agent)
        kwargs.setdefault('headers', {}).update(self.headers)
        if isinstance(data, dict):
            if encode:
                data = self._encodeRPCRequest(method, data)
            resp = self._post(self._url(method), json=data or {}, **kwargs)
        else:
            resp = self._post(self._url(method), data=data, **kwargs)
        if raw:
            return resp
        if stream:
            try:
                return self._modelizeStreamResponse(method, resp)
            except Etcd3Exception:
                resp.close()
        return self._modelizeResponse(method, resp)

    async def auth(self, username=None, password=None):
        """
        call auth.authenticate and save the token

        :type username: str
        :param username: username
        :type password: str
        :param password: password
        """
        username = username or self.username
        password = password or self.password
        old = self.token
        self.token = None
        try:
            r = await self.authenticate(username, password)
        except Exception:  # pragma: no cover
            self.token = old
            raise
        else:
            self.username = username
            self.password = password
            self.token = r.token
