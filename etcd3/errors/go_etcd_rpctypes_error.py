"""
from github.com/coreos/etcd/etcdserver/api/v3rpc/rpctypes/error.go
"""

from .go_grpc_codes import GRPCCode, codeText

# server-side error
ErrGRPCEmptyKey = GRPCCode.InvalidArgument, "etcdserver: key is not provided"
ErrGRPCKeyNotFound = GRPCCode.InvalidArgument, "etcdserver: key not found"
ErrGRPCValueProvided = GRPCCode.InvalidArgument, "etcdserver: value is provided"
ErrGRPCLeaseProvided = GRPCCode.InvalidArgument, "etcdserver: lease is provided"
ErrGRPCTooManyOps = GRPCCode.InvalidArgument, "etcdserver: too many operations in txn request"
ErrGRPCDuplicateKey = GRPCCode.InvalidArgument, "etcdserver: duplicate key given in txn request"
ErrGRPCCompacted = GRPCCode.OutOfRange, "etcdserver: mvcc: required revision has been compacted"
ErrGRPCFutureRev = GRPCCode.OutOfRange, "etcdserver: mvcc: required revision is a future revision"
ErrGRPCNoSpace = GRPCCode.ResourceExhausted, "etcdserver: mvcc: database space exceeded"

ErrGRPCLeaseNotFound = GRPCCode.NotFound, "etcdserver: requested lease not found"
ErrGRPCLeaseExist = GRPCCode.FailedPrecondition, "etcdserver: lease already exists"
ErrGRPCLeaseTTLTooLarge = GRPCCode.OutOfRange, "etcdserver: too large lease TTL"

ErrGRPCMemberExist = GRPCCode.FailedPrecondition, "etcdserver: member ID already exist"
ErrGRPCPeerURLExist = GRPCCode.FailedPrecondition, "etcdserver: Peer URLs already exists"
ErrGRPCMemberNotEnoughStarted = GRPCCode.FailedPrecondition, "etcdserver: re-configuration failed due to not enough started members"
ErrGRPCMemberBadURLs = GRPCCode.InvalidArgument, "etcdserver: given member URLs are invalid"
ErrGRPCMemberNotFound = GRPCCode.NotFound, "etcdserver: member not found"

ErrGRPCRequestTooLarge = GRPCCode.InvalidArgument, "etcdserver: request is too large"
ErrGRPCRequestTooManyRequests = GRPCCode.ResourceExhausted, "etcdserver: too many requests"

ErrGRPCRootUserNotExist = GRPCCode.FailedPrecondition, "etcdserver: root user does not exist"
ErrGRPCRootRoleNotExist = GRPCCode.FailedPrecondition, "etcdserver: root user does not have root role"
ErrGRPCUserAlreadyExist = GRPCCode.FailedPrecondition, "etcdserver: user name already exists"
ErrGRPCUserEmpty = GRPCCode.InvalidArgument, "etcdserver: user name is empty"
ErrGRPCUserNotFound = GRPCCode.FailedPrecondition, "etcdserver: user name not found"
ErrGRPCRoleAlreadyExist = GRPCCode.FailedPrecondition, "etcdserver: role name already exists"
ErrGRPCRoleNotFound = GRPCCode.FailedPrecondition, "etcdserver: role name not found"
ErrGRPCAuthFailed = GRPCCode.InvalidArgument, "etcdserver: authentication failed, invalid user ID or password"
ErrGRPCPermissionDenied = GRPCCode.PermissionDenied, "etcdserver: permission denied"
ErrGRPCRoleNotGranted = GRPCCode.FailedPrecondition, "etcdserver: role is not granted to the user"
ErrGRPCPermissionNotGranted = GRPCCode.FailedPrecondition, "etcdserver: permission is not granted to the role"
ErrGRPCAuthNotEnabled = GRPCCode.FailedPrecondition, "etcdserver: authentication is not enabled"
ErrGRPCInvalidAuthToken = GRPCCode.Unauthenticated, "etcdserver: invalid auth token"
ErrGRPCInvalidAuthMgmt = GRPCCode.InvalidArgument, "etcdserver: invalid auth management"

ErrGRPCNoLeader = GRPCCode.Unavailable, "etcdserver: no leader"
ErrGRPCNotLeader = GRPCCode.FailedPrecondition, "etcdserver: not leader"
ErrGRPCNotCapable = GRPCCode.Unavailable, "etcdserver: not capable"
ErrGRPCStopped = GRPCCode.Unavailable, "etcdserver: server stopped"
ErrGRPCTimeout = GRPCCode.Unavailable, "etcdserver: request timed out"
ErrGRPCTimeoutDueToLeaderFail = GRPCCode.Unavailable, "etcdserver: request timed out, possibly due to previous leader failure"
ErrGRPCTimeoutDueToConnectionLost = GRPCCode.Unavailable, "etcdserver: request timed out, possibly due to connection lost"
ErrGRPCUnhealthy = GRPCCode.Unavailable, "etcdserver: unhealthy cluster"
ErrGRPCCorrupt = GRPCCode.DataLoss, "etcdserver: corrupt cluster"

error_desc = lambda e: e[1]

errStringToError = {
    error_desc(ErrGRPCEmptyKey): ErrGRPCEmptyKey,
    error_desc(ErrGRPCKeyNotFound): ErrGRPCKeyNotFound,
    error_desc(ErrGRPCValueProvided): ErrGRPCValueProvided,
    error_desc(ErrGRPCLeaseProvided): ErrGRPCLeaseProvided,

    error_desc(ErrGRPCTooManyOps): ErrGRPCTooManyOps,
    error_desc(ErrGRPCDuplicateKey): ErrGRPCDuplicateKey,
    error_desc(ErrGRPCCompacted): ErrGRPCCompacted,
    error_desc(ErrGRPCFutureRev): ErrGRPCFutureRev,
    error_desc(ErrGRPCNoSpace): ErrGRPCNoSpace,

    error_desc(ErrGRPCLeaseNotFound): ErrGRPCLeaseNotFound,
    error_desc(ErrGRPCLeaseExist): ErrGRPCLeaseExist,
    error_desc(ErrGRPCLeaseTTLTooLarge): ErrGRPCLeaseTTLTooLarge,

    error_desc(ErrGRPCMemberExist): ErrGRPCMemberExist,
    error_desc(ErrGRPCPeerURLExist): ErrGRPCPeerURLExist,
    error_desc(ErrGRPCMemberNotEnoughStarted): ErrGRPCMemberNotEnoughStarted,
    error_desc(ErrGRPCMemberBadURLs): ErrGRPCMemberBadURLs,
    error_desc(ErrGRPCMemberNotFound): ErrGRPCMemberNotFound,

    error_desc(ErrGRPCRequestTooLarge): ErrGRPCRequestTooLarge,
    error_desc(ErrGRPCRequestTooManyRequests): ErrGRPCRequestTooManyRequests,

    error_desc(ErrGRPCRootUserNotExist): ErrGRPCRootUserNotExist,
    error_desc(ErrGRPCRootRoleNotExist): ErrGRPCRootRoleNotExist,
    error_desc(ErrGRPCUserAlreadyExist): ErrGRPCUserAlreadyExist,
    error_desc(ErrGRPCUserEmpty): ErrGRPCUserEmpty,
    error_desc(ErrGRPCUserNotFound): ErrGRPCUserNotFound,
    error_desc(ErrGRPCRoleAlreadyExist): ErrGRPCRoleAlreadyExist,
    error_desc(ErrGRPCRoleNotFound): ErrGRPCRoleNotFound,
    error_desc(ErrGRPCAuthFailed): ErrGRPCAuthFailed,
    error_desc(ErrGRPCPermissionDenied): ErrGRPCPermissionDenied,
    error_desc(ErrGRPCRoleNotGranted): ErrGRPCRoleNotGranted,
    error_desc(ErrGRPCPermissionNotGranted): ErrGRPCPermissionNotGranted,
    error_desc(ErrGRPCAuthNotEnabled): ErrGRPCAuthNotEnabled,
    error_desc(ErrGRPCInvalidAuthToken): ErrGRPCInvalidAuthToken,
    error_desc(ErrGRPCInvalidAuthMgmt): ErrGRPCInvalidAuthMgmt,

    error_desc(ErrGRPCNoLeader): ErrGRPCNoLeader,
    error_desc(ErrGRPCNotLeader): ErrGRPCNotLeader,
    error_desc(ErrGRPCNotCapable): ErrGRPCNotCapable,
    error_desc(ErrGRPCStopped): ErrGRPCStopped,
    error_desc(ErrGRPCTimeout): ErrGRPCTimeout,
    error_desc(ErrGRPCTimeoutDueToLeaderFail): ErrGRPCTimeoutDueToLeaderFail,
    error_desc(ErrGRPCTimeoutDueToConnectionLost): ErrGRPCTimeoutDueToConnectionLost,
    error_desc(ErrGRPCUnhealthy): ErrGRPCUnhealthy,
    error_desc(ErrGRPCCorrupt): ErrGRPCCorrupt,
}


# client-side error
class Etcd3Exception(Exception):
    pass


def Error(err, name):
    class ClientError(Etcd3Exception):
        def __init__(self, error, code, status, response=None):
            self.code = err[0]
            self.error = err[1]
            self.codeText = codeText[code]
            self.status = status
            self.response = response

        def __repr__(self):
            return "<%s error:'%s', code:%s>" % (self.__class__.__name__, self.error, self.code)

        __str__ = __repr__

        def as_dict(self):
            return {
                'error': self.error,
                'code': self.code,
                'codeText': self.codeText,
                'status': self.status
            }

    ClientError.__name__ = name

    return ClientError


class ErrUnknownError(Error((GRPCCode.Unknown, codeText[GRPCCode.Unknown]), 'ErrUnknownError')):
    def __init__(self, error, code, status, response=None):
        self.code = code
        self.error = error.strip()
        self.codeText = codeText[code]
        self.status = status
        self.response = response


ErrEmptyKey = Error(ErrGRPCEmptyKey, 'ErrEmptyKey')
ErrKeyNotFound = Error(ErrGRPCKeyNotFound, 'ErrKeyNotFound')
ErrValueProvided = Error(ErrGRPCValueProvided, 'ErrValueProvided')
ErrLeaseProvided = Error(ErrGRPCLeaseProvided, 'ErrLeaseProvided')
ErrTooManyOps = Error(ErrGRPCTooManyOps, 'ErrTooManyOps')
ErrDuplicateKey = Error(ErrGRPCDuplicateKey, 'ErrDuplicateKey')
ErrCompacted = Error(ErrGRPCCompacted, 'ErrCompacted')
ErrFutureRev = Error(ErrGRPCFutureRev, 'ErrFutureRev')
ErrNoSpace = Error(ErrGRPCNoSpace, 'ErrNoSpace')

ErrLeaseNotFound = Error(ErrGRPCLeaseNotFound, 'ErrLeaseNotFound')
ErrLeaseExist = Error(ErrGRPCLeaseExist, 'ErrLeaseExist')
ErrLeaseTTLTooLarge = Error(ErrGRPCLeaseTTLTooLarge, 'ErrLeaseTTLTooLarge')

ErrMemberExist = Error(ErrGRPCMemberExist, 'ErrMemberExist')
ErrPeerURLExist = Error(ErrGRPCPeerURLExist, 'ErrPeerURLExist')
ErrMemberNotEnoughStarted = Error(ErrGRPCMemberNotEnoughStarted, 'ErrMemberNotEnoughStarted')
ErrMemberBadURLs = Error(ErrGRPCMemberBadURLs, 'ErrMemberBadURLs')
ErrMemberNotFound = Error(ErrGRPCMemberNotFound, 'ErrMemberNotFound')

ErrRequestTooLarge = Error(ErrGRPCRequestTooLarge, 'ErrRequestTooLarge')
ErrTooManyRequests = Error(ErrGRPCRequestTooManyRequests, 'ErrTooManyRequests')

ErrRootUserNotExist = Error(ErrGRPCRootUserNotExist, 'ErrRootUserNotExist')
ErrRootRoleNotExist = Error(ErrGRPCRootRoleNotExist, 'ErrRootRoleNotExist')
ErrUserAlreadyExist = Error(ErrGRPCUserAlreadyExist, 'ErrUserAlreadyExist')
ErrUserEmpty = Error(ErrGRPCUserEmpty, 'ErrUserEmpty')
ErrUserNotFound = Error(ErrGRPCUserNotFound, 'ErrUserNotFound')
ErrRoleAlreadyExist = Error(ErrGRPCRoleAlreadyExist, 'ErrRoleAlreadyExist')
ErrRoleNotFound = Error(ErrGRPCRoleNotFound, 'ErrRoleNotFound')
ErrAuthFailed = Error(ErrGRPCAuthFailed, 'ErrAuthFailed')
ErrPermissionDenied = Error(ErrGRPCPermissionDenied, 'ErrPermissionDenied')
ErrRoleNotGranted = Error(ErrGRPCRoleNotGranted, 'ErrRoleNotGranted')
ErrPermissionNotGranted = Error(ErrGRPCPermissionNotGranted, 'ErrPermissionNotGranted')
ErrAuthNotEnabled = Error(ErrGRPCAuthNotEnabled, 'ErrAuthNotEnabled')
ErrInvalidAuthToken = Error(ErrGRPCInvalidAuthToken, 'ErrInvalidAuthToken')
ErrInvalidAuthMgmt = Error(ErrGRPCInvalidAuthMgmt, 'ErrInvalidAuthMgmt')

ErrNoLeader = Error(ErrGRPCNoLeader, 'ErrNoLeader')
ErrNotLeader = Error(ErrGRPCNotLeader, 'ErrNotLeader')
ErrNotCapable = Error(ErrGRPCNotCapable, 'ErrNotCapable')
ErrStopped = Error(ErrGRPCStopped, 'ErrStopped')
ErrTimeout = Error(ErrGRPCTimeout, 'ErrTimeout')
ErrTimeoutDueToLeaderFail = Error(ErrGRPCTimeoutDueToLeaderFail, 'ErrTimeoutDueToLeaderFail')
ErrTimeoutDueToConnectionLost = Error(ErrGRPCTimeoutDueToConnectionLost, 'ErrTimeoutDueToConnectionLost')
ErrUnhealthy = Error(ErrGRPCUnhealthy, 'ErrUnhealthy')
ErrCorrupt = Error(ErrGRPCCorrupt, 'ErrCorrupt')

errStringToClientError = {
    error_desc(ErrGRPCEmptyKey): ErrEmptyKey,
    error_desc(ErrGRPCKeyNotFound): ErrKeyNotFound,
    error_desc(ErrGRPCValueProvided): ErrValueProvided,
    error_desc(ErrGRPCLeaseProvided): ErrLeaseProvided,

    error_desc(ErrGRPCTooManyOps): ErrTooManyOps,
    error_desc(ErrGRPCDuplicateKey): ErrDuplicateKey,
    error_desc(ErrGRPCCompacted): ErrCompacted,
    error_desc(ErrGRPCFutureRev): ErrFutureRev,
    error_desc(ErrGRPCNoSpace): ErrNoSpace,

    error_desc(ErrGRPCLeaseNotFound): ErrLeaseNotFound,
    error_desc(ErrGRPCLeaseExist): ErrLeaseExist,
    error_desc(ErrGRPCLeaseTTLTooLarge): ErrLeaseTTLTooLarge,

    error_desc(ErrGRPCMemberExist): ErrMemberExist,
    error_desc(ErrGRPCPeerURLExist): ErrPeerURLExist,
    error_desc(ErrGRPCMemberNotEnoughStarted): ErrMemberNotEnoughStarted,
    error_desc(ErrGRPCMemberBadURLs): ErrMemberBadURLs,
    error_desc(ErrGRPCMemberNotFound): ErrMemberNotFound,

    error_desc(ErrGRPCRequestTooLarge): ErrRequestTooLarge,
    error_desc(ErrGRPCRequestTooManyRequests): ErrTooManyRequests,

    error_desc(ErrGRPCRootUserNotExist): ErrRootUserNotExist,
    error_desc(ErrGRPCRootRoleNotExist): ErrRootRoleNotExist,
    error_desc(ErrGRPCUserAlreadyExist): ErrUserAlreadyExist,
    error_desc(ErrGRPCUserEmpty): ErrUserEmpty,
    error_desc(ErrGRPCUserNotFound): ErrUserNotFound,
    error_desc(ErrGRPCRoleAlreadyExist): ErrRoleAlreadyExist,
    error_desc(ErrGRPCRoleNotFound): ErrRoleNotFound,
    error_desc(ErrGRPCAuthFailed): ErrAuthFailed,
    error_desc(ErrGRPCPermissionDenied): ErrPermissionDenied,
    error_desc(ErrGRPCRoleNotGranted): ErrRoleNotGranted,
    error_desc(ErrGRPCPermissionNotGranted): ErrPermissionNotGranted,
    error_desc(ErrGRPCAuthNotEnabled): ErrAuthNotEnabled,
    error_desc(ErrGRPCInvalidAuthToken): ErrInvalidAuthToken,
    error_desc(ErrGRPCInvalidAuthMgmt): ErrInvalidAuthMgmt,

    error_desc(ErrGRPCNoLeader): ErrNoLeader,
    error_desc(ErrGRPCNotLeader): ErrNotLeader,
    error_desc(ErrGRPCNotCapable): ErrNotCapable,
    error_desc(ErrGRPCStopped): ErrStopped,
    error_desc(ErrGRPCTimeout): ErrTimeout,
    error_desc(ErrGRPCTimeoutDueToLeaderFail): ErrTimeoutDueToLeaderFail,
    error_desc(ErrGRPCTimeoutDueToConnectionLost): ErrTimeoutDueToConnectionLost,
    error_desc(ErrGRPCUnhealthy): ErrUnhealthy,
    error_desc(ErrGRPCCorrupt): ErrCorrupt,
}
