import os
import shlex

from etcd3.utils import exec_cmd, find_executable
from .envs import ETCD_IMG

DOCKER_PATH = find_executable('docker')
CERTS_DIR = os.path.join(os.path.dirname(__file__), 'certs')

SERVER_CA_PATH = '/certs/ca.pem'
SERVER_CERT_PATH = '/certs/server.pem'
SERVER_KEY_PATH = '/certs/server-key.pem'

CA_PATH = os.path.join(CERTS_DIR, 'ca.pem')
CERT_PATH = os.path.join(CERTS_DIR, 'client.pem')
KEY_PATH = os.path.join(CERTS_DIR, 'client-key.pem')


def docker(*args, **kwargs):  # pragma: no cover
    if len(args) == 1:
        args = shlex.split(args[0])
    raise_error = kwargs.get('raise_error', True)
    envs = os.environ
    cmd = [DOCKER_PATH]
    cmd.extend(args)
    return exec_cmd(cmd, envs, raise_error)


# get the etcd server's http port and tcp peer port
def get_h_t(n):  # pragma: no cover
    h = 2380 + n  # the http port
    t = h + 1  # the tcp peer port
    return h, t


def docker_run_etcd(n=2):  # pragma: no cover
    n = n or 2  # the node sequence
    h, t = get_h_t(n)
    cmd = 'run -d -p {h}:{h} -p {t}:{t} --name etcd3_{n} ' \
          '{img} ' \
          'etcd --name node{n} ' \
          '--initial-advertise-peer-urls http://0.0.0.0:{t} ' \
          '--listen-peer-urls http://0.0.0.0:{t} ' \
          '--advertise-client-urls http://0.0.0.0:{h} ' \
          '--listen-client-urls http://0.0.0.0:{h} ' \
          '--initial-cluster node{n}=http://0.0.0.0:{t}'.format(n=n, h=h, t=t, img=ETCD_IMG)
    print(cmd)
    return docker(cmd), h, t


def docker_rm_etcd(n=2):  # pragma: no cover
    n = n or 2  # the node sequence
    cmd = 'rm -f etcd3_{n}'.format(n=n)
    return docker(cmd)


def get_ssl_ht_t():  # pragma: no cover
    return get_h_t(10)


def docker_run_etcd_ssl():  # pragma: no cover
    n = 10  # the node sequence
    h, t = get_h_t(n)
    cmd = 'run -d -p {h}:{h} -p {t}:{t} --name etcd3_ssl -v {certs_dir}:/certs ' \
          '{img} ' \
          'etcd --name node_ssl ' \
          '--client-cert-auth ' \
          '--trusted-ca-file={ca} ' \
          '--cert-file={cer} ' \
          '--key-file={key} ' \
          '--initial-advertise-peer-urls http://0.0.0.0:{t} ' \
          '--listen-peer-urls http://0.0.0.0:{t} ' \
          '--advertise-client-urls https://0.0.0.0:{h} ' \
          '--listen-client-urls https://0.0.0.0:{h} ' \
          '--initial-cluster node_ssl=http://0.0.0.0:{t}' \
        .format(n=n, h=h, t=t, img=ETCD_IMG,
                certs_dir=CERTS_DIR,
                ca=SERVER_CA_PATH,
                cer=SERVER_CERT_PATH,
                key=SERVER_KEY_PATH)
    print(cmd)
    return docker(cmd), h, t


def docker_rm_etcd_ssl(raise_error=False): # pragma: no cover
    cmd = 'rm -f etcd3_ssl'
    return docker(cmd, raise_error=raise_error)


NO_DOCKER_SERVICE = True
try:  # pragma: no cover
    if DOCKER_PATH and docker('version'):
        NO_DOCKER_SERVICE = False
    else:
        print("docker executable not found")
except Exception as e:  # pragma: no cover
    print(e)

if __name__ == '__main__':
    docker_run_etcd_ssl()
