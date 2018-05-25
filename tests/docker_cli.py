import time

import json
import os
import shlex
import six

from etcd3.utils import find_executable, exec_cmd
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
    # return subprocess.check_call(cmd, env=envs)
    return exec_cmd(cmd, envs, raise_error)


# get the etcd server's http port and tcp peer port
def get_h_t(n):  # pragma: no cover
    h = 2379 + 2 * (n - 1)  # the http port
    t = h + 1  # the tcp peer port
    return h, t


def docker_run_etcd_main():  # pragma: no cover
    if NO_DOCKER_SERVICE:
        return None, 2379, None
    n = 1
    h, t = get_h_t(n)  # 2379, 2380
    name = 'etcd3_1'
    try:
        out = docker('inspect %s' % name)
        if isinstance(out, six.binary_type):
            out = six.text_type(out, encoding='utf-8')
        spec = json.loads(out)
        if isinstance(spec, list):
            spec = spec[0]
        image = spec.get('Config', {}).get('Image')
        if image != ETCD_IMG or not spec.get('State', {}).get('Running'):
            if spec.get('Config', {}).get('Labels', {}).get('etcd3.py.test') == 'main':
                print(docker('rm -f %s' % name))
            raise RuntimeError
        cmds = spec.get('Config', {}).get('Cmd', [])
        for i, c in enumerate(cmds):
            if c == '--listen-client-urls':
                h = int(cmds[i + 1].split(':')[-1])
            if c == '--listen-peer-urls':
                t = int(cmds[i + 1].split(':')[-1])
        return '', h, t
    except:
        cmd = 'run -d -p {h}:{h} -p {t}:{t} --name {name} ' \
              '-l etcd3.py.test=main ' \
              '{img} ' \
              'etcd --name node{n} ' \
              '--initial-advertise-peer-urls http://0.0.0.0:{t} ' \
              '--listen-peer-urls http://0.0.0.0:{t} ' \
              '--advertise-client-urls http://0.0.0.0:{h} ' \
              '--listen-client-urls http://0.0.0.0:{h} ' \
              '--initial-cluster node{n}=http://0.0.0.0:{t}'.format(name=name, n=n, h=h, t=t, img=ETCD_IMG)
        print(cmd)
        out = docker(cmd)
        print(out)
        time.sleep(5)
        return out, h, t


def docker_run_etcd(n=2):  # pragma: no cover
    n = n or 2  # the node sequence
    h, t = get_h_t(n)
    cmd = 'run -d -p {h}:{h} -p {t}:{t} --name etcd3_{n} ' \
          '-l etcd3.py.test=node{n} ' \
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
          '-l etcd3.py.test=node{n} ' \
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


def docker_rm_etcd_ssl(raise_error=False):  # pragma: no cover
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
