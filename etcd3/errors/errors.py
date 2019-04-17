import six

from .go_etcd_rpctypes_error import Etcd3Exception, errStringToClientError, ErrUnknownError


class Etcd3StreamError(Etcd3Exception):  # pragma: no cover
    def __init__(self, error, buf, resp):
        self.error = error
        self.buf = buf
        self.resp = resp


class Etcd3WatchCanceled(Etcd3Exception):  # pragma: no cover
    def __init__(self, error, resp):
        self.error = error
        self.resp = resp


def get_client_error(error, code, status, response=None):
    if six.PY3 and not isinstance(error, six.string_types):
        error = six.text_type(error, encoding='utf-8')
    err = errStringToClientError.get(error)
    if not err:
        err = ErrUnknownError
    return err(error, code, status, response)


class UnsupportedServerVersion(Etcd3Exception):
    pass
