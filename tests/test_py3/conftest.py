import pytest
from etcd3 import AioClient


@pytest.fixture
async def aio_client(event_loop, request, etcd_cluster):
    """
    init Etcd3Client, close its connection-pool when teardown
    """

    c = AioClient(endpoints=etcd_cluster.get_endpoints(),
                  protocol='https' if etcd_cluster.ssl else 'http')

    def teardown():
        async def _t():
            await c.close()

        event_loop.run_until_complete(_t())
        event_loop._close()

    request.addfinalizer(teardown)
    return c
