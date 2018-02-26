import json
import os

import requests
import six
from six.moves import urllib_parse

from .apis import AuthAPI
from .apis import ClusterAPI
from .apis import KVAPI
from .apis import LeaseAPI
from .apis import MaintenanceAPI
from .apis import WatchAPI
from .errors import Etcd3APIError, Etcd3Exception
from .errors import Etcd3StreamError
from .swagger_helper import SwaggerSpec
from .version import __version__

rpc_swagger_json = os.path.join(os.path.dirname(__file__), 'rpc.swagger.json')

swaggerSpec = SwaggerSpec(rpc_swagger_json)


class ModelizedStreamResponse(object):
    def __init__(self, method, resp, decode=True):
        """
        :param resp: Response
        """
        self.resp = resp
        self.decode = decode
        self.method = method

    def close(self):
        return self.resp.close()

    def __iter__(self):
        swpath = swaggerSpec.getPath(self.method)
        respModel = swpath.post.responses._200.schema.getModel()
        for data in iter_response(self.resp):
            if not data:
                continue
            data = json.loads(data)
            if data.get('error'):
                # {"error":{"grpc_code":14,"http_code":503,"message":"rpc error: code = Unavailable desc = transport is closing","http_status":"Service Unavailable"}}
                err = data.get('error')
                raise Etcd3APIError(err.get('message'), code=err.get('code'), status=err.get('http_code'))
            data = data.get('result', {})  # the real data is put under the key: 'result'
            if self.decode:
                data = Etcd3APIClient.decodeRPCResponse(self.method, data)
            yield respModel(data)


def iter_response(resp):
    """
    yield response content by every json object
    we don't yield by line, because the content of etcd's gRPC-JSON-Gateway stream response
    does not have a delimiter between each object by default. (only one line)
    https://github.com/grpc-ecosystem/grpc-gateway/pull/497/files
    :param resp: Response
    :return: dict
    """
    buf = []
    bracket_flag = 0
    for c in resp.iter_content(chunk_size=1):
        if six.PY3:
            c = six.text_type(c, encoding='utf-8')
        buf.append(c)
        if c == '{':
            bracket_flag += 1
        elif c == '}':
            bracket_flag -= 1
        if bracket_flag == 0:
            s = ''.join(buf)
            buf = []
            yield s
        elif bracket_flag < 0:
            raise Etcd3StreamError("Stream decode error", buf, resp)


class Etcd3APIClient(AuthAPI, ClusterAPI, KVAPI, LeaseAPI, MaintenanceAPI, WatchAPI):
    response_class = requests.models.Response

    def __init__(self, host='localhost', port=2379, protocol='http',
                 ca_cert=None, cert_key=None, cert_cert=None,
                 timeout=None, headers=None, user_agent=None, pool_size=30,
                 user=None, password=None, token=None):
        self.session = requests.session()
        self.__set_conn_pool(pool_size)
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
        self.user = user
        self.password = password
        self.token = token

    def __set_conn_pool(self, pool_size):
        pass

    @property
    def baseurl(self):
        return '{}://{}:{}'.format(self.protocol, self.host, self.port)

    def _url(self, method):
        return urllib_parse.urljoin(self.baseurl, method)

    def encodeRPCRequest(self, method, data):
        swpath = swaggerSpec.getPath(method)
        if not swpath:
            return data
        reqSchema = swpath.post.parameters[0].schema
        return reqSchema.encode(data)

    @classmethod
    def decodeRPCResponse(cls, method, data):
        if isinstance(data, cls.response_class):
            data = data.json()
        swpath = swaggerSpec.getPath(method)
        if not swpath:
            return data
        reqSchema = swpath.post.responses._200.schema
        return reqSchema.decode(data)

    @classmethod
    def modelizeStreamResponse(cls, method, resp, decode=True):
        return ModelizedStreamResponse(method, resp, decode)

    @classmethod
    def modelizeResponse(cls, method, resp, decode=True):
        if isinstance(resp, cls.response_class):
            resp = resp.json()
        if decode:
            resp = cls.decodeRPCResponse(method, resp)
        swpath = swaggerSpec.getPath(method)
        respModel = swpath.post.responses._200.schema.getModel()
        return respModel(resp)

    @staticmethod
    def raise_for_status(resp):
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
        raise Etcd3APIError(error, code, status, resp)

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
        data = data or {}
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('cert', self.cert)
        kwargs.setdefault('headers', {}).setdefault('user_agent', self.user_agent)
        kwargs.setdefault('headers', {}).update(self.headers)
        if encode:
            data = self.encodeRPCRequest(method, data)
        resp = self.session.post(self._url(method), json=data or {}, stream=stream, **kwargs)
        self.raise_for_status(resp)
        if raw:
            return resp
        if stream:
            try:
                return self.modelizeStreamResponse(method, resp)
            except Etcd3Exception:
                resp.close()
        return self.modelizeResponse(method, resp)
