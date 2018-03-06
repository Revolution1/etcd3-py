from collections import namedtuple

from .base import BaseAPI

EtcdVersion = namedtuple('EtcdVersion', ['etcdserver', 'etcdcluster'])


class ExtraAPI(BaseAPI):
    def version(self):
        """
        get the version of etcdserver and etcdcluster

        :return: EtcdVersion
        """
        resp = self._get(self._url('/version'))
        self._raise_for_status(resp)
        return EtcdVersion(**resp.json())

    def metrics_raw(self):
        """
        get the raw /metrics text

        :return: str
        """
        resp = self._get(self._url('/metrics'))
        self._raise_for_status(resp)
        return resp.content

    def metrics(self):
        """
        get the modelized metrics parsed by prometheus_client
        """
        from prometheus_client.parser import text_string_to_metric_families

        return text_string_to_metric_families(self.metrics_raw())
