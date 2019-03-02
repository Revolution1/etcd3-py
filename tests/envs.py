import logging
import os

logging.basicConfig(format='%(name)s %(levelname)s - %(message)s')
log = logging.getLogger()
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
log.addHandler(handler)

ETCD_VER = os.getenv('ETCD_VER') or 'v3.3.0'

ETCD_IMG = 'quay.io/coreos/etcd:' + ETCD_VER

DOCKER_PUBLISH_HOST = '127.0.0.1'


CERTS_DIR = os.path.join(os.path.dirname(__file__), 'certs')
CA_PATH = os.path.join(CERTS_DIR, 'ca.pem')
CERT_PATH = os.path.join(CERTS_DIR, 'client.pem')
KEY_PATH = os.path.join(CERTS_DIR, 'client-key.pem')
SERVER_CA_PATH = '/certs/ca.pem'
SERVER_CERT_PATH = '/certs/server.pem'
SERVER_KEY_PATH = '/certs/server-key.pem'

NO_DOCKER_SERVICE = True
try:  # pragma: no cover
    import docker  # noqa
    NO_DOCKER_SERVICE = False
except ImportError as e:  # pragma: no cover
    print("docker library not found")
    print(e)
