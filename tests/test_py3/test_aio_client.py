import pytest

from etcd3 import AioClient
from ..envs import protocol, host, port
from ..etcd_go_cli import NO_ETCD_SERVICE
from ..etcd_go_cli import etcdctl


@pytest.fixture
async def aio_client(event_loop):
    """
    init Etcd3Client, close its connection-pool when teardown
    """

    with AioClient(host, port, protocol) as c:
        return c


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
@pytest.mark.asyncio
async def test_async_request_and_model(aio_client):
    etcdctl('put test_key test_value')
    result = await aio_client.call_rpc('/v3alpha/kv/range', {'key': 'test_key'})
    # {"header":{"cluster_id":11588568905070377092,"member_id":128088275939295631,"revision":3,"raft_term":2},"kvs":[{"key":"dGVzdF9rZXk=","create_revision":3,"mod_revision":3,"version":1,"value":"dGVzdF92YWx1ZQ=="}],"count":1}'
    assert result.kvs[0].key == b'test_key'
    assert result.kvs[0].value == b'test_value'
    etcdctl('del test_key')


@pytest.mark.skipif(NO_ETCD_SERVICE, reason="no etcd service available")
@pytest.mark.asyncio
async def test_async_stream(aio_client):
    r = await aio_client.call_rpc('/v3alpha/watch', {'create_request': {'key': 'test_key'}}, stream=True)
    times = 3
    header_times = 1
    async for i in r:
        if not times:
            break
        etcdctl('put test_key test_value')
        if hasattr(i, 'events'):
            assert i.events[0].kv.key == b'test_key'
            assert i.events[0].kv.value == b'test_value'
            times -= 1
        else:
            header_times -= 1
            assert header_times >= 0
