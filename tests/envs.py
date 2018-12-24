import logging
import os
from six.moves.urllib_parse import urlparse

logging.basicConfig(format='%(name)s %(levelname)s - %(message)s')
log = logging.getLogger()
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
log.addHandler(handler)

ETCD_ENDPOINT = os.getenv('ETCD_ENDPOINT') or 'http://localhost:2379'
_url = urlparse(ETCD_ENDPOINT)

protocol = _url.scheme

host, port = _url.netloc.split(':')

ETCD_VER = os.getenv('ETCD_VER') or 'v3.3.0'

ETCD_IMG = 'quay.io/coreos/etcd:' + ETCD_VER
