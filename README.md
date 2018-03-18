etcd3-py
---------------------

[![pypi](https://img.shields.io/pypi/v/etcd3-py.svg)](https://pypi.python.org/pypi/etcd3-py)
[![travis](https://travis-ci.org/Revolution1/etcd3-py.svg?branch=master)](https://travis-ci.org/Revolution1/etcd3-py)
[![codecov](https://codecov.io/gh/Revolution1/etcd3-py/branch/master/graph/badge.svg)](https://codecov.io/gh/Revolution1/etcd3-py)
[![doc](https://readthedocs.org/projects/etcd3-py/badge/?version=latest)](http://etcd3-py.readthedocs.io/en/latest/?badge=latest)
[![updates](https://pyup.io/repos/github/Revolution1/etcd3-py/shield.svg)](https://pyup.io/repos/github/Revolution1/etcd3-py/)
[![python3](https://pyup.io/repos/github/Revolution1/etcd3-py/python-3-shield.svg)](https://pyup.io/repos/github/Revolution1/etcd3-py/)

Python client for etcd v3 (Using gRPC-JSON-Gateway)

* Free software: Apache Software License 2.0
* Documentation: https://etcd3-py.readthedocs.io.

Notice: The authentication header through gRPC-JSON-Gateway only supported in [etcd v3.3+](https://github.com/coreos/etcd/pull/7999)

Features
========

* [x] Support python2.7 and python3.5+
* [x] Sync client based on requests
* [x] Async client based on aiohttp
* [x] Support etcd3 gRPC-JSON-Gateway including stream
* [x] Response modelizing based on etcd3's swagger spec
* [x] Generate code from swagger spec
* [ ] TLS Connection
* [x] support APIs
    * [x] Auth
    * [x] KV
    * [x] Watch
    * [x] Cluster
    * [x] Lease
    * [x] Maintenance
    * [x] Extra APIs
* [ ] stateful utilities
    * [ ] Watch
    * [ ] Lease
    * [ ] Transaction
    * [ ] Lock

Quick Start
===========

**Install**
```bash
$ pip install etcd3-py
```

**Sync Client**
```python
>>> from etcd3 import Client
>>> client = Client('127.0.0.1', 2379)
>>> client.version()
EtcdVersion(etcdserver='3.3.0-rc.4', etcdcluster='3.3.0')
>>> client.put('foo', 'bar')
etcdserverpbPutResponse(header=etcdserverpbResponseHeader(cluster_id=11588568905070377092, member_id=128088275939295631, revision=15433, raft_term=4))
>>> client.range('foo').kvs
[mvccpbKeyValue(key=b'foo', create_revision=15429, mod_revision=15433, version=5, value=b'bar')]
```

**Async Client (Python3.5+)**
```python
>>> import asyncio
>>> from etcd3 import AioClient
>>> client = AioClient('127.0.0.1', 2379)
>>> async def getFoo():
...     await client.put('foo', 'bar')
...     r = await client.range('foo')
...     print('key:', r.kvs[0].key, 'value:', r.kvs[0].value)
>>> loop = asyncio.get_event_loop()
>>> loop.run_until_complete(getFoo())
key: b'foo' value: b'bar'
```


TODO
====

- [ ] benchmark
- [ ] python-etcd(etcd v2) compatible client
- [ ] etcd browser
