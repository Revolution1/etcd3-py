class BaseAPI(object):  # pragma: no cover
    def __init__(self):
        self.headers = {}

    @staticmethod
    def _raise_for_status(resp):
        raise NotImplementedError

    def _url(self, method, prefix=True):
        raise NotImplementedError

    def _get(self, url, **kwargs):
        raise NotImplementedError

    def _post(self, url, data=None, json=None, **kwargs):
        raise NotImplementedError

    def call_rpc(self, method, data=None, stream=False, encode=True, raw=False, **kwargs):
        raise NotImplementedError
