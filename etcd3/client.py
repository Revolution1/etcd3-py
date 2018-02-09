import json
import os
import sys
import traceback

import requests
from six.moves import urllib_parse

from __version__ import __version__
from apis import BaseAPI
from errors import Etcd3Exception
from swagger_helper import SwaggerSpec

rpc_swagger_json = os.path.join(os.path.dirname(__file__), 'rpc.swagger.json')

swaggerSpec = SwaggerSpec(rpc_swagger_json)


def iter_response(resp):
    """
    yield response content by every json object
    we don't yield by line, because the content of gRPC-JSON-Gateway stream response
    does not have a delimiter  between each object by default.
    https://github.com/grpc-ecosystem/grpc-gateway/pull/497/files
    :param resp: Response
    :return: dict
    """
    buf = []
    bracket_flag = 0
    for c in resp.iter_content():
        buf.append(c)
        if c == '{':
            bracket_flag += 1
        elif c == '}':
            bracket_flag -= 1
        if bracket_flag == 0:
            s = ''.join(buf)
            buf = []
            if s:
                yield json.loads(s)


class Etcd3APIClient(BaseAPI):
    response_class = requests.models.Response

    def __init__(self, host='localhost', port=2379, protocol='http',
                 ca_cert=None, cert_key=None, cert_cert=None,
                 timeout=None, headers=None, user_agent=None, pool_size=30,
                 user=None, password=None, token=None):
        self.session = requests.session()
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
        swpath = swaggerSpec.getPath(method)
        respModel = swpath.post.responses._200.schema.getModel()
        for data in iter_response(resp):
            data = data.get('result', {})  # the real data is been put under the key: 'result'
            if decode:
                data = cls.decodeRPCResponse(method, data)
            yield respModel(data)

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
        except:
            _, _, tb = sys.exc_info()
            error = ''.join(traceback.format_tb(tb))
            code = -1
        else:
            error = data.get('error')
            code = data.get('code')
        raise Etcd3Exception(error, code, status)

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
            return self.modelizeStreamResponse(method, resp)
        return self.modelizeResponse(method, resp)


if __name__ == '__main__':
    client = Etcd3APIClient()
    # print(client.call_rpc('/v3alpha/maintenance/status').json())
    # print(client.call_rpc('/v3alpha/kv/put', {'key': 'foo', 'value': 'bar'}).json())
    # print(client.call_rpc('/v3alpha/kv/put', {'key': 'foo', 'value': 'bar', 'prev_kv': True}).json())
    # print(client.call_rpc('/v3alpha/kv/range', {'key': 'foo'}).json())
    # print(client.call_rpc('/v3alpha/kv/range', {'key': 'foa'}).json())
    r = client.call_rpc('/v3alpha/watch', {'create_request': {'key': 'foo'}}, stream=True)
    for i in r:
        print(i)
    print(client.call_rpc('/v3alpha/kv/rang', {'key': 'foa'}).json())
