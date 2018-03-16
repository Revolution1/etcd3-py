from .base import BaseAPI
from ..utils import check_param


class WatchAPI(BaseAPI):
    @check_param(at_least_one_of=['create_request', 'cancel_request'],
                 at_most_one_of=['create_request', 'cancel_request'])
    def watch(self, create_request=None, cancel_request=None):
        """
        PLEASE USE THE WATCH UTIL

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
        data = {
            "create_request": create_request,
            "cancel_request": cancel_request
        }
        data = {k: v for k, v in data.items() if v is not None}

        # data = {
        #     "create_request": {
        #         "key": "string",
        #         "range_end": "string",
        #         "start_revision": "string",
        #         "progress_notify": True,
        #         "filters": [
        #             "NOPUT"
        #         ],
        #         "prev_kv": True
        #     },
        #     "cancel_request": {
        #         "watch_id": "string"
        #     }
        # }
        return self.call_rpc(method, data=data, stream=True)
