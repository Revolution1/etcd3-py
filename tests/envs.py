import os

ETCD_ENDPOINT = os.getenv('ETCD_ENDPOINT') or 'http://0.0.0.0:2379'
