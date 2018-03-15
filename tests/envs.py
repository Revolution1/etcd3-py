import os

from six.moves.urllib_parse import urlparse

ETCD_ENDPOINT = os.getenv('ETCD_ENDPOINT') or 'http://127.0.0.1:2379'
_url = urlparse(ETCD_ENDPOINT)

protocol = _url.scheme

host, port = _url.netloc.split(':')
