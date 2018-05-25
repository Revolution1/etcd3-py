import shlex

from etcd3.utils import exec_cmd, find_executable
from tests.docker_cli import NO_DOCKER_SERVICE
from .envs import ETCD_ENDPOINT

ETCDCTL_PATH = find_executable('etcdctl')


def etcdctl(*args, **kwargs):  # pragma: no cover
    if len(args) == 1:
        args = shlex.split(args[0])
    json = kwargs.get('json', False)
    endpoint = kwargs.get('endpoint', ETCD_ENDPOINT)
    version = kwargs.get('version', 3)
    raise_error = kwargs.get('raise_error', True)

    envs = {}
    cmd = [ETCDCTL_PATH, '--endpoints', endpoint]
    if json:
        cmd.extend(['-w', 'json'])
    if version == 3:
        envs['ETCDCTL_API'] = '3'
    cmd.extend(args)
    return exec_cmd(cmd, envs, raise_error)


NO_ETCD_SERVICE = True
if not NO_DOCKER_SERVICE:
    NO_ETCD_SERVICE = False
try:  # pragma: no cover
    if ETCDCTL_PATH and etcdctl('--dial-timeout=0.2s endpoint health'):
        NO_ETCD_SERVICE = False
    else:
        print("etcdctl executable not found")
except Exception as e:  # pragma: no cover
    print(e)

if __name__ == '__main__':
    print(etcdctl('get foo'))
