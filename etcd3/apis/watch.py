from .base import BaseAPI


class WatchAPI(BaseAPI):
    def watch(self, create_request, cancel_request):
        """
        Watch watches for events happening or that have happened. Both input and output
        are streams; the input stream is for creating and canceling watchers and the output
        stream sends events. One watch RPC can watch on multiple key ranges, streaming events
        for several watches at once. The entire event history can be watched starting from the
        last compaction revision.

        :type create_request: dict
        :param create_request: None
        :type cancel_request: dict
        :param cancel_request: None
        """
        method = '/v3alpha/watch'
        data = {}
        return self.call_rpc(method, data=data)
