"""
synchronous client
"""

import json

import requests
import six

from .baseclient import BaseClient
from .baseclient import BaseModelizedStreamResponse
from .baseclient import DEFAULT_VERSION
from .errors import Etcd3Exception
from .errors import Etcd3StreamError
from .errors import get_client_error
from .utils import iter_json_string


class ModelizedStreamResponse(BaseModelizedStreamResponse):
    """
    Model of a stream response
    """

    def __init__(self, client, method, resp, decode=True):
        """
        :param resp: Response
        """
        self.client = client
        self.method = method
        self.resp = resp
        self.decode = decode

    @property
    def raw(self):
        return self.resp.raw

    def close(self):
        """
        close the stream
        """
        return self.resp.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    #
    # def __del__(self):
    #     self.close()

    def __iter__(self):
        for data in iter_response(self.resp):
            if not data:
                continue
            if six.PY3:
                data = six.text_type(data, encoding='utf-8')
            data = json.loads(data)
            if data.get('error'):  # pragma: no cover
                # {"error":{"grpc_code":14,"http_code":503,"message":"rpc error: code = Unavailable desc = transport is closing","http_status":"Service Unavailable"}}
                err = data.get('error')
                raise get_client_error(err.get('message'), code=err.get('code'), status=err.get('http_code'))
            r = self.client._modelizeResponseData(self.method, data, decode=self.decode)
            if r.result:
                r = r.result
            yield r


def iter_response(resp):
    """
    yield response content by every json object
    we don't yield by line, because the content of etcd's gRPC-JSON-Gateway stream response
    does not have a delimiter between each object by default. (only one line)

    https://github.com/grpc-ecosystem/grpc-gateway/pull/497/files

    :param resp: Response
    :return: dict
    """
    left_chunk = b''
    # https://github.com/coreos/etcd/blob/master/etcdserver/api/v3rpc/maintenance.go#L98
    # 2**15 < ceil(32*1024/3*4) < 2**16 = 65536
    for chunk in resp.iter_content(chunk_size=65536):
        chunk = chunk.strip()
        chunk = left_chunk + chunk
        for ok, s, _ in iter_json_string(chunk, resp=resp, err_cls=Etcd3StreamError):
            if ok:
                yield s
            else:
                left_chunk = s
    if left_chunk:  # pragma: no cover
        raise Etcd3StreamError("Stream decode error", left_chunk, resp)


class Client(BaseClient):
    def __init__(self, host='127.0.0.1', port=2379, protocol='http',
                 cert=(), verify=None,
                 timeout=None, headers=None, user_agent=None, pool_size=30,
                 username=None, password=None, token=None, max_retries=0,
                 server_version=DEFAULT_VERSION, cluster_version=DEFAULT_VERSION):
        """
        :param max_retries: The maximum number of retries each connection
            should attempt. Note, this applies only to failed DNS lookups, socket
            connections and connection timeouts, never to requests where data has
            made it to the server. By default, Requests does not retry failed
            connections. If you need granular control over the conditions under
            which we retry a request, import urllib3's ``Retry`` class and pass
            that instead.
        """
        super(Client, self).__init__(host=host, port=port, protocol=protocol,
                                     cert=cert, verify=verify,
                                     timeout=timeout, headers=headers, user_agent=user_agent, pool_size=pool_size,
                                     username=username, password=password, token=token,
                                     server_version=server_version, cluster_version=cluster_version)
        self._session = requests.session()
        self._session.cert = self.cert
        self._session.verify = self.verify
        self.__set_conn_pool(pool_size, max_retries)

    def __set_conn_pool(self, pool_size, max_retries):
        # aiohttp does not support a max_retries param like requests
        # For now we just mark it as a TODO feature
        from requests.adapters import HTTPAdapter
        adapter = HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size, max_retries=max_retries)
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)

    def close(self):
        """
        close all connections in connection pool
        """
        return self._session.close()

    def _modelizeStreamResponse(self, method, resp, decode=True):
        return ModelizedStreamResponse(self, method, resp, decode)

    @staticmethod
    def _raise_for_status(resp):
        status = resp.status_code
        if status < 400:
            return
        try:
            data = resp.json()
        except Exception:
            error = resp.content
            code = 2
        else:
            error = data.get('error')
            code = data.get('code')
        raise get_client_error(error, code, status, resp)

    def _get(self, url, **kwargs):
        r"""
        Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        return self._session.get(url, **kwargs)

    def _post(self, url, data=None, json=None, **kwargs):
        r"""
        Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        return self._session.post(url, data=data, json=json, **kwargs)

    def call_rpc(self, method, data=None, stream=False, encode=True, raw=False, **kwargs):  # TODO: add modelize param
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
        data = data or {}
        kwargs.setdefault('timeout', self.timeout)
        if self.token:
            kwargs.setdefault('headers', {}).setdefault('authorization', self.token)
        kwargs.setdefault('headers', {}).setdefault('user_agent', self.user_agent)
        for k, v in self.headers.items():
            kwargs.setdefault('headers', {}).setdefault(k, v)
        if isinstance(data, dict):
            if encode:
                data = self._encodeRPCRequest(method, data)
            resp = self._post(self._url(method), json=data or {}, stream=stream, **kwargs)
        else:
            resp = self._post(self._url(method), data=data, stream=stream, **kwargs)
        self._raise_for_status(resp)
        if raw:
            return resp
        if stream:
            try:
                return self._modelizeStreamResponse(method, resp)
            except Etcd3Exception:
                resp.close()
        return self._modelizeResponseData(method, resp.json())

    def auth(self, username=None, password=None):
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
            r = self.authenticate(username, password)
        except Exception:
            self.token = old
            raise
        else:
            self.username = username
            self.password = password
            self.token = r.token
