import asyncio
import pytest
from etcd3 import AioClient
from ..envs import CERT_PATH
from ..envs import KEY_PATH
from ..envs import CA_PATH
from ..envs import NO_DOCKER_SERVICE


@pytest.fixture
def event_loop():  # pragma: no cover
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    res = policy.new_event_loop()
    asyncio.set_event_loop(res)
    res._close = res.close
    res.close = lambda: None
    return res


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
@pytest.mark.asyncio
async def test_async_request_and_model(aio_client, etcd_cluster):
    etcd_cluster.etcdctl('put test_key test_value')
    result = await aio_client.call_rpc('/kv/range', {'key': 'test_key'})
    # {"header":{"cluster_id":11588568905070377092,"member_id":128088275939295631,"revision":3,"raft_term":2},"kvs":[{"key":"dGVzdF9rZXk=","create_revision":3,"mod_revision":3,"version":1,"value":"dGVzdF92YWx1ZQ=="}],"count":1}'
    assert result.kvs[0].key == b'test_key'
    assert result.kvs[0].value == b'test_value'
    etcd_cluster.etcdctl('del test_key')


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
@pytest.mark.asyncio
async def test_async_stream(aio_client, etcd_cluster):
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
            etcd_cluster.etcdctl('put test_key test_value')
            if i.events:
                assert i.events[0].kv.key == b'test_key'
                assert i.events[0].kv.value == b'test_value'
                times -= 1


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
@pytest.mark.asyncio
async def test_aio_client_ssl(etcd_cluster_ssl):
    aio_client = AioClient(endpoints=etcd_cluster_ssl.get_endpoints(),
                           cert=(CERT_PATH, KEY_PATH), verify=CA_PATH)
    assert await aio_client.call_rpc('/kv/range', {'key': 'test_key'})


@pytest.mark.skipif(NO_DOCKER_SERVICE, reason="no docker service available")
@pytest.mark.asyncio
async def test_aio_client_host_port(etcd_cluster_ssl):
    endpoint = etcd_cluster_ssl.get_endpoints()[0]
    aio_client = AioClient(host=endpoint.host, port=endpoint.port,
                           cert=(CERT_PATH, KEY_PATH), verify=CA_PATH)
    assert await aio_client.call_rpc('/kv/range', {'key': 'test_key'})
