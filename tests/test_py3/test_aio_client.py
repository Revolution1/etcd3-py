import asyncio
import time

import pytest

from etcd3 import AioClient
from ..docker_cli import docker_rm_etcd_ssl, docker_run_etcd_ssl, CERT_PATH, KEY_PATH, CA_PATH, NO_DOCKER_SERVICE, \
    docker_run_etcd_main
from ..envs import protocol, host
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


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
@pytest.mark.asyncio
async def test_async_request_and_model(aio_client):
    etcdctl('put test_key test_value')
    result = await aio_client.call_rpc('/kv/range', {'key': 'test_key'})
    # {"header":{"cluster_id":11588568905070377092,"member_id":128088275939295631,"revision":3,"raft_term":2},"kvs":[{"key":"dGVzdF9rZXk=","create_revision":3,"mod_revision":3,"version":1,"value":"dGVzdF92YWx1ZQ=="}],"count":1}'
    assert result.kvs[0].key == b'test_key'
    assert result.kvs[0].value == b'test_value'
    etcdctl('del test_key')


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
@pytest.mark.asyncio
async def test_async_stream(aio_client):
    times = 20
    created = False
    # async with and with both works
    async with aio_client.call_rpc('/watch', {'create_request': {'key': 'test_key'}}, stream=True) as r:
        async for i in r:
            if not times:
                break
            if not created:
                created = i.created
                assert created
            etcdctl('put test_key test_value')
            if i.events:
                assert i.events[0].kv.key == b'test_key'
                assert i.events[0].kv.value == b'test_value'
                times -= 1


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
@pytest.mark.asyncio
async def test_aio_client_ssl():
    docker_rm_etcd_ssl()
    _, port, _ = docker_run_etcd_ssl()
    time.sleep(2)
    aio_client = AioClient(host, port, cert=(CERT_PATH, KEY_PATH), verify=CA_PATH)
    assert await aio_client.call_rpc('/kv/range', {'key': 'test_key'})
    docker_rm_etcd_ssl()
