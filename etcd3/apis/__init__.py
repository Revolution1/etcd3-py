from abc import abstractmethod, ABCMeta

import six


@six.add_metaclass(ABCMeta)
class BaseAPI(object):
    @abstractmethod
    def call_rpc(self, method, data=None, stream=False, **kwargs):
        pass
