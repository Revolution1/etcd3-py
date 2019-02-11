from collections import namedtuple

import six

from .base import BaseAPI

EtcdVersion = namedtuple('EtcdVersion', ['etcdserver', 'etcdcluster'])


class ExtraAPI(BaseAPI):
    def version(self):
        """
        get the version of etcdserver and etcdcluster

        :return: EtcdVersion
        """
        resp = self._get(self._url('/version', prefix=False), headers=self.headers)
        self._raise_for_status(resp)
        return EtcdVersion(**resp.json())

    def health(self):
        """
        get the health of etcd-server

        :return: EtcdVersion
        """
        resp = self._get(self._url('/health', prefix=False), headers=self.headers)
        self._raise_for_status(resp)
        return resp.json()['health']

    def metrics_raw(self):  # pragma: no cover
        """
        get the raw /metrics text

        :return: str
        """
        resp = self._get(self._url('/metrics', prefix=False), headers=self.headers)
        self._raise_for_status(resp)
        metrics = resp.content
        if not isinstance(metrics, six.text_type):
            metrics = six.text_type(metrics, encoding='utf-8')
        return metrics

    def metrics(self):  # pragma: no cover
        """
        get the modelized metrics parsed by prometheus_client
        """
        from prometheus_client.parser import text_string_to_metric_families

        return text_string_to_metric_families(self.metrics_raw())
