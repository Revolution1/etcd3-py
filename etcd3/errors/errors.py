from go_grpc_codes import codeText


class Etcd3Exception(Exception):
    def __init__(self, error, code, status):
        self.code = code
        self.codeText = codeText[code]
        self.status = status
        self.error = error

    def __repr__(self):
        return "Etcd3Exception(code='%s', message='%s')" % (self.code, self.error)

    def as_dict(self):
        return {
            'error': self.error,
            'code': self.code,
            'codeText': self.codeText,
            'status': self.status
        }
