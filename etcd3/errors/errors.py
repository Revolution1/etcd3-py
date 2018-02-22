from go_grpc_codes import codeText


class Etcd3Exception(Exception):
    pass


class Etcd3APIError(Etcd3Exception):
    def __init__(self, error, code, status, response=None):
        self.code = code
        self.codeText = codeText[code]
        self.status = status
        self.error = error.strip()
        self.response = response

    def __repr__(self):
        return "<Etcd3APIError error:'%s', code:%s>" % (self.error, self.code)

    __str__ = __repr__

    def as_dict(self):
        return {
            'error': self.error,
            'code': self.code,
            'codeText': self.codeText,
            'status': self.status
        }


class Etcd3StreamError(Etcd3Exception):
    def __init__(self, error, buf, resp):
        self.error = error
        self.buf = buf
        self.resp = resp
