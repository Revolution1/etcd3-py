import asyncio

import logging
import pytest
import re

from ..envs import ETCD_VER
from ..envs import NO_DOCKER_SERVICE
from ..conftest import teardown_auth
from ..conftest import enable_auth


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
async def test_async_client_auth(aio_client, etcd_cluster, request):
    teardown_auth(etcd_cluster)
    enable_auth(etcd_cluster)
    request.addfinalizer(lambda: teardown_auth(etcd_cluster))

    # test client auth
    await aio_client.auth('root', 'root')
    assert aio_client.token
    if re.match(r'v?3\.[0-2]\.{0,1}', ETCD_VER):  # pragma: no cover
        logging.info('skipping tests of apis with auth enabled, cause etcd < v3.3.0 does not support auth header')
    else:
        assert await aio_client.user_get('root')
