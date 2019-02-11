import asyncio

import logging
import pytest
import re

from etcd3 import AioClient
from tests.docker_cli import docker_run_etcd_main
from ..envs import protocol, host, ETCD_VER
from ..etcd_go_cli import NO_ETCD_SERVICE
from ..etcd_go_cli import etcdctl


@pytest.fixture
def event_loop():  # pragma: no cover
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    res = policy.new_event_loop()
    asyncio.set_event_loop(res)
    res._close = res.close
    res.close = lambda: None
    return res


@pytest.fixture
async def aio_client(event_loop, request):
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    _, p, _ = docker_run_etcd_main()
    c = AioClient(host, p, protocol)

    def teardown():
        async def _t():
            await c.close()

        event_loop.run_until_complete(_t())
        event_loop._close()

    request.addfinalizer(teardown)
    return c


def teardown_auth():  # pragma: no cover
    """
    disable auth, delete all users and roles
    """
    etcdctl('--user root:root auth disable', raise_error=False)
    etcdctl('--user root:changed auth disable', raise_error=False)
    for i in (etcdctl('role list', raise_error=False) or '').splitlines():
        etcdctl('role', 'delete', i)
    for i in (etcdctl('user list', raise_error=False) or '').splitlines():
        etcdctl('user', 'delete', i)


def enable_auth():  # pragma: no cover
    etcdctl('user add root:root')
    etcdctl('role add root')
    etcdctl('user grant root root')
    etcdctl('auth enable')


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
@pytest.mark.asyncio
async def test_async_client_auth(aio_client, request):
    teardown_auth()
    enable_auth()
    request.addfinalizer(teardown_auth)

    # test client auth
    await aio_client.auth('root', 'root')
    assert aio_client.token
    if re.match(r'v?3\.[0-2]\.{0,1}', ETCD_VER):  # pragma: no cover
        logging.info('skipping tests of apis with auth enabled, cause etcd < v3.3.0 does not support auth header')
    else:
        assert await aio_client.user_get('root')
