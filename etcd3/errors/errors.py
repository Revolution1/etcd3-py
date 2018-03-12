from .go_etcd_rpctypes_error import Etcd3Exception, errStringToClientError, ErrUnknownError


class Etcd3StreamError(Etcd3Exception):
    def __init__(self, error, buf, resp):
        self.error = error
        self.buf = buf
        self.resp = resp


def get_client_error(error, code, status, response=None):
    err = errStringToClientError.get(error)
    if not err:
        err = ErrUnknownError
    return err(error, code, status, response)
