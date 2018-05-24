# etcd3-py

[![pypi](https://img.shields.io/pypi/v/etcd3-py.svg)](https://pypi.python.org/pypi/etcd3-py)
[![travis](https://travis-ci.org/Revolution1/etcd3-py.svg?branch=master)](https://travis-ci.org/Revolution1/etcd3-py)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9448814cd66b4a568365bc050d88270c)](https://www.codacy.com/app/revol/etcd3-py?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Revolution1/etcd3-py&amp;utm_campaign=Badge_Grade)
[![codecov](https://codecov.io/gh/Revolution1/etcd3-py/branch/master/graph/badge.svg)](https://codecov.io/gh/Revolution1/etcd3-py)
[![doc](https://readthedocs.org/projects/etcd3-py/badge/?version=latest)](http://etcd3-py.readthedocs.io/en/latest/?badge=latest)
[![updates](https://pyup.io/repos/github/Revolution1/etcd3-py/shield.svg)](https://pyup.io/repos/github/Revolution1/etcd3-py/)
[![python3](https://pyup.io/repos/github/Revolution1/etcd3-py/python-3-shield.svg)](https://pyup.io/repos/github/Revolution1/etcd3-py/)

Python client for etcd v3 (Using gRPC-JSON-Gateway)

* Free software: Apache Software License 2.0
* Source Code: https://github.com/Revolution1/etcd3-py
* Documentation: https://etcd3-py.readthedocs.io.
* etcd version required: v3.2.2+

Notice: The authentication header through gRPC-JSON-Gateway only supported in [etcd v3.3.0+](https://github.com/coreos/etcd/pull/7999)

## Features

* [x] Support python2.7 and python3.5+
* [x] Sync client based on requests
* [x] Async client based on aiohttp
* [x] TLS Connection
* [x] support APIs
    * [x] Auth
    * [x] KV
    * [x] Watch
    * [x] Cluster
    * [x] Lease
    * [x] Maintenance
    * [x] Extra APIs
* [x] stateful utilities
    * [x] Watch
    * [x] Lease
    * [x] Transaction
    * [x] Lock

## Quick Start

**Install**
```bash
$ pip install etcd3-py
```

**Sync Client**
```python
>>> from etcd3 import Client
>>> client = Client('127.0.0.1', 2379, cert=(CERT_PATH, KEY_PATH), verify=CA_PATH)
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

**Transaction Util**
```python
>>> from etcd3 import Client
>>> txn = Client().Txn()
>>> txn.compare(txn.key('foo').value == 'bar')
>>> txn.success(txn.put('foo', 'bra'))
>>> txn.commit()
etcdserverpbTxnResponse(header=etcdserverpbResponseHeader(cluster_id=11588568905070377092, member_id=128088275939295631, revision=15656, raft_term=4), succeeded=True, responses=[etcdserverpbResponseOp(response_put=etcdserverpbPutResponse(header=etcdserverpbResponseHeader(revision=15656)))])
```

**Lease Util**
```python
>>> from etcd3 import Client
>>> client = Client()
>>> with client.Lease(ttl=5) as lease:
...     client.put('foo', 'bar', lease=lease.ID)
...     client.put('fizz', 'buzz', lease=lease.ID)
...     r = lease.time_to_live(keys=True)
...     assert set(r.keys) == {b'foo', b'fizz'}
...     assert lease.alive()
```

**Watch Util**
```python
>>> from etcd3 import Client
>>> client = Client()
>>> watcher = c.Watcher(all=True, progress_notify=True, prev_kv=True)
>>> w.onEvent('f.*', lambda e: print(e.key, e.value))
>>> w.runDaemon()
>>> # etcdctl put foo bar
>>> # etcdctl put foz bar
b'foo' b'bar'
b'foz' b'bar'
>>> w.stop()
```

**Lock Util**
```python
>>> import time
>>> from threading import Thread
>>> from etcd3 import Client
>>> client = Client()
>>> name = 'lock_name'
>>> def user1():
...     with client.Lock(name, lock_ttl=5):
...         print('user1 got the lock')
...         time.sleep(5)
...         print('user1 releasing the lock')
>>> def user2():
...     with client.Lock(name, lock_ttl=5):
...         print('user2 got the lock')
...         time.sleep(5)
...         print('user2 releasing the lock')
>>> t1 = Thread(target=user1, daemon=True)
>>> t2 = Thread(target=user2, daemon=True)
>>> t1.start()
>>> t2.start()
>>> t1.join()
>>> t2.join()
user1 got the lock
user1 releasing the lock
user2 got the lock
user2 releasing the lock
```

**Start a single-node etcd using docker**
```bash
export NODE1=0.0.0.0
export ETCD_VER=v3.3
docker run -d \
-p 2379:2379 \
-p 2380:2380 \
--volume=/tmp/etcd3-data:/etcd-data \
--name etcd3 quay.io/coreos/etcd:$ETCD_VER \
/usr/local/bin/etcd \
--data-dir=/etcd-data --name node1 \
--initial-advertise-peer-urls http://${NODE1}:2380 --listen-peer-urls http://${NODE1}:2380 \
--advertise-client-urls http://${NODE1}:2379 --listen-client-urls http://${NODE1}:2379 \
--initial-cluster node1=http://${NODE1}:2380
```

## TODO

- [ ] benchmark
- [ ] python-etcd(etcd v2) compatible client
- [ ] etcd browser
