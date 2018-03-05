class BaseAPI(object):
    @staticmethod
    def _raise_for_status(resp):
        raise NotImplementedError

    def _url(self, method):
        raise NotImplementedError

    def _get(self, url, **kwargs):
        raise NotImplementedError

    def _post(self, url, data=None, json=None, **kwargs):
        raise NotImplementedError

    def call_rpc(self, method, data=None, stream=False, **kwargs):
        raise NotImplementedError
