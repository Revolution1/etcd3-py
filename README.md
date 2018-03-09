etcd3-py (Developing)
---------------------

[![pypi](https://img.shields.io/pypi/v/etcd3-py.svg)](https://pypi.python.org/pypi/etcd3-py)
[![travis](https://travis-ci.org/Revolution1/etcd3-py.svg?branch=master)](https://travis-ci.org/Revolution1/etcd3-py)
[![doc](https://readthedocs.org/projects/etcd3-py/badge/?version=latest)](http://etcd3-py.readthedocs.io/en/latest/?badge=latest)
[![updates](https://pyup.io/repos/github/Revolution1/etcd3-py/shield.svg)](https://pyup.io/repos/github/Revolution1/etcd3-py/)
[![python3](https://pyup.io/repos/github/Revolution1/etcd3-py/python-3-shield.svg)](https://pyup.io/repos/github/Revolution1/etcd3-py/)

Python client for etcd v3 (Using grpc-json-gateway)

* Free software: Apache Software License 2.0
* Documentation: https://etcd3.readthedocs.io.


Features
========

* [x] support python2 and python3.5+
* [x] sync client based on requests
* [x] async client based on aiohttp
* [x] support etcd3 gRPC-JSON-Gateway including stream
* [x] response modelizing based on etcd3's swagger spec
* [x] generate code from swagger spec
* [x] auto unit testing
* [ ] support APIs
    * [ ] KV
    * [ ] Watch
    * [ ] Cluster
    * [ ] Lease
    * [ ] Maintenance
    * [ ] Auth
    * [ ] Extra APIs

Quick Start
===========

**Async Client**
```python
>>> from etcd3 import Client
>>> client = Client('127.0.0.1', 2379)
>>> client.version()
EtcdVersion(etcdserver='3.3.0-rc.4', etcdcluster='3.3.0')
```
