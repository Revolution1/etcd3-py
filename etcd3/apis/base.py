class BaseAPI(object):
    def call_rpc(self, method, data=None, stream=False, **kwargs):
        raise NotImplementedError
