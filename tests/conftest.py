from etcd3.client import Client
import pytest
from .etcd_cluster import EtcdTestCluster


@pytest.fixture(scope='session')
def etcd_cluster(request):
    # function_name = request.function.__name__
    # function_name = re.sub(r"[^a-zA-Z0-9]+", "", function_name)
    cluster = EtcdTestCluster(ident='cleartext', size=3)

    def fin():
        cluster.down()
    request.addfinalizer(fin)
    cluster.up()
    cluster.wait_ready()

    return cluster


@pytest.fixture(scope='session')
def etcd_cluster_ssl(request):
    # function_name = request.function.__name__
    # function_name = re.sub(r"[^a-zA-Z0-9]+", "", function_name)
    cluster = EtcdTestCluster(ident='ssl', size=3, ssl=True)

    def fin():
        cluster.down()
    request.addfinalizer(fin)
    cluster.up()
    cluster.wait_ready()

    return cluster


@pytest.fixture(scope='module')
def client(etcd_cluster):
    """
    init Etcd3Client, close its connection-pool when teardown
    """
    # _, p, _ = docker_run_etcd_main()
    c = Client(endpoints=etcd_cluster.get_endpoints(),
               protocol='https' if etcd_cluster.ssl else 'http')
    yield c
    c.close()


@pytest.fixture
def clear(etcd_cluster):
    def _clear():
        etcd_cluster.etcdctl('del --from-key ""')
    return _clear


def teardown_auth(etcd_cluster):  # pragma: no cover
    """
    disable auth, delete all users and roles
    """
    etcd_cluster.etcdctl('--user root:root auth disable')
    etcd_cluster.etcdctl('--user root:changed auth disable')
    for i in (etcd_cluster.etcdctl('role list') or '').splitlines():
        etcd_cluster.etcdctl('role delete %s' % i)
    for i in (etcd_cluster.etcdctl('user list') or '').splitlines():
        etcd_cluster.etcdctl('user delete %s' % i)


def enable_auth(etcd_cluster):  # pragma: no cover
    etcd_cluster.etcdctl('user add root:root')
    etcd_cluster.etcdctl('role add root')
    etcd_cluster.etcdctl('user grant root root')
    etcd_cluster.etcdctl('auth enable')
