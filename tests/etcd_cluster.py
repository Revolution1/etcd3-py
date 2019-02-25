import docker
from etcd3.utils import EtcdEndpoint
from .envs import ETCD_IMG
from .envs import DOCKER_PUBLISH_HOST
from .envs import CERTS_DIR
from .envs import SERVER_CA_PATH
from .envs import SERVER_CERT_PATH
from .envs import SERVER_KEY_PATH
from time import sleep
import copy
import logging
import six

log = logging.getLogger(__name__)


class EtcdTestCluster:
    def __init__(self, ident, size, ssl=False):
        self.containers = []
        self.network = None
        self.ident = ident
        self.size = size
        self.ssl = ssl
        self.client = docker.from_env()

    def etcdctl(self, command, container_idx=None):
        if container_idx:
            exec_containers = [self.containers[container_idx]]
        else:
            exec_containers = copy.copy(self.containers)
        cmd = '%s %s' % (self.etcdctl_command(), command)
        for c in exec_containers:
            try:
                out = c.exec_run(cmd)
                if out.exit_code != 0:
                    log.warning('executing etcdctl command on %s returned %s' %
                                (cmd, out))
                    continue
                return out.output
            except Exception as e:
                log.warn('error executing etcdctl command %s on %s: %s' %
                         (cmd, c.name, e))
        raise Exception("error executing etcdctl command %s on all containers" %
                        cmd)

    def etcdctl_command(self):
        command = "etcdctl"
        if self.ssl:
            command += " --key /certs/client-key.pem"
            command += " --cert /certs/client.pem"
            command += " --endpoints=https://127.0.0.1:2379"
            command += " --insecure-skip-tls-verify"
        return command

    def is_container_ready(self, container):
        try:
            command = '%s endpoint status' % self.etcdctl_command()
            out = container.exec_run(command)
            if out.exit_code != 0:
                return False
            return True
        except Exception:
            sleep(1)
            return False

    def wait_container_ready(self, container):
        while not self.is_container_ready(container):
            sleep(0.5)
        idx = self.containers.index(container)
        # log.error(self.etcdctl("endpoint status"))
        sleep(0.5)

    def wait_ready(self):
        while True:
            sleep(0.5)
            out = self.etcdctl('version')
            if six.PY3:  # pragma: no cover
                out = six.text_type(out, encoding='utf-8')
            if 'not_decided' in out:
                continue
            out = self.etcdctl('member list')
            if len([x for x in out.splitlines() if b'started' in x]) == self.size:
                return

    def get_endpoints(self):
        for c in self.containers:
            c.reload()
        return [EtcdEndpoint(
            DOCKER_PUBLISH_HOST,
            c.attrs['NetworkSettings']['Ports']['2379/tcp'][0]['HostPort'])
            for c in self.containers]

    def get_endpoints_param(self):
        addresses = [
            c.attrs['NetworkSettings']['Networks']["etcd-%s" % self.ident]['IPAddress']
            for c in self.containers]
        return "--endpoints=%s" % ",".join(["%s:2379" % a for a in addresses])

    def down(self):
        for c in self.containers:
            c.remove(force=True)
        if self.network:
            self.network.remove()

    def rolling_restart(self):
        for c in self.containers:
            log.info('killing container %s' % c.name)
            c.kill()
            log.info('waiting for container %s to be ready' % c.name)
            self.wait_container_ready(c)

    def up(self):
        self.network = self.client.networks.create(name="etcd-%s" % self.ident)
        image_found = False
        for image in self.client.images.list():
            if ETCD_IMG in image.tags:
                image_found = True
        if not image_found:
            log.info('pulling image %s' % ETCD_IMG)
            self.client.images.pull(ETCD_IMG)
        initial_cluster = ','.join(
            ["etcd{x}-{n}=http://etcd{x}-{n}:2380".format(n=self.ident, x=x)
             for x in range(self.size)])
        if self.ssl:
            ssl_opts = [
                '--client-cert-auth',
                '--cert-file=%s' % SERVER_CERT_PATH,
                '--key-file=%s' % SERVER_KEY_PATH,
                '--trusted-ca-file=%s' % SERVER_CA_PATH,
                '--listen-client-urls=https://0.0.0.0:2379',
                '--advertise-client-urls=https://0.0.0.0:2379']
        else:
            ssl_opts = [
                '--listen-client-urls=http://0.0.0.0:2379',
                '--advertise-client-urls=http://0.0.0.0:2379']
        self.containers = [
            self.client.containers.create(
                name="etcd%s-%s" % (i, self.ident),
                image=ETCD_IMG,
                environment={
                    'ETCDCTL_API': '3',
                },
                command=['etcd', '--name=etcd%s-%s' % (i, self.ident),
                         '--listen-peer-urls=http://0.0.0.0:2380',
                         '--initial-cluster', initial_cluster,
                         ] + ssl_opts,
                ports={'2379/tcp': None},
                volumes={
                    CERTS_DIR: {'bind': '/certs', 'mode': 'ro'},
                    "/tmp/shared": {'bind': '/tmp/shared', 'mode': 'rw'},
                    },
                network=self.network.name,
            )
            for i in range(self.size)]
        for c in self.containers:
            log.debug('starting container %s' % c.name)
            c.start()
        for c in self.containers:
            log.debug('wait for container %s to be ready' % c.name)
            self.wait_container_ready(c)
            c.reload()
