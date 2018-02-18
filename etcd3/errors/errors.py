from go_grpc_codes import codeText


class Etcd3Exception(Exception):
    def __init__(self, error, code, status):
        self.code = code
        self.codeText = codeText[code]
        self.status = status
        self.error = error.strip()

    def __repr__(self):
        return "<Etcd3Exception error:'%s', code:%s>" % (self.error, self.code)

    __str__ = __repr__

    def as_dict(self):
        return {
            'error': self.error,
            'code': self.code,
            'codeText': self.codeText,
            'status': self.status
        }
