# flake8: noqa
from .errors import Etcd3StreamError
from .errors import get_client_error
from .go_etcd_rpctypes_error import ErrAuthFailed
from .go_etcd_rpctypes_error import ErrAuthNotEnabled
from .go_etcd_rpctypes_error import ErrCompacted
from .go_etcd_rpctypes_error import ErrCorrupt
from .go_etcd_rpctypes_error import ErrDuplicateKey
from .go_etcd_rpctypes_error import ErrEmptyKey
from .go_etcd_rpctypes_error import ErrFutureRev
from .go_etcd_rpctypes_error import ErrInvalidAuthMgmt
from .go_etcd_rpctypes_error import ErrInvalidAuthToken
from .go_etcd_rpctypes_error import ErrKeyNotFound
from .go_etcd_rpctypes_error import ErrLeaseExist
from .go_etcd_rpctypes_error import ErrLeaseNotFound
from .go_etcd_rpctypes_error import ErrLeaseProvided
from .go_etcd_rpctypes_error import ErrLeaseTTLTooLarge
from .go_etcd_rpctypes_error import ErrMemberBadURLs
from .go_etcd_rpctypes_error import ErrMemberExist
from .go_etcd_rpctypes_error import ErrMemberNotEnoughStarted
from .go_etcd_rpctypes_error import ErrMemberNotFound
from .go_etcd_rpctypes_error import ErrNoLeader
from .go_etcd_rpctypes_error import ErrNoSpace
from .go_etcd_rpctypes_error import ErrNotCapable
from .go_etcd_rpctypes_error import ErrNotLeader
from .go_etcd_rpctypes_error import ErrPeerURLExist
from .go_etcd_rpctypes_error import ErrPermissionDenied
from .go_etcd_rpctypes_error import ErrPermissionNotGranted
from .go_etcd_rpctypes_error import ErrRequestTooLarge
from .go_etcd_rpctypes_error import ErrRoleAlreadyExist
from .go_etcd_rpctypes_error import ErrRoleNotFound
from .go_etcd_rpctypes_error import ErrRoleNotGranted
from .go_etcd_rpctypes_error import ErrRootRoleNotExist
from .go_etcd_rpctypes_error import ErrRootUserNotExist
from .go_etcd_rpctypes_error import ErrStopped
from .go_etcd_rpctypes_error import ErrTimeout
from .go_etcd_rpctypes_error import ErrTimeoutDueToConnectionLost
from .go_etcd_rpctypes_error import ErrTimeoutDueToLeaderFail
from .go_etcd_rpctypes_error import ErrTooManyOps
from .go_etcd_rpctypes_error import ErrTooManyRequests
from .go_etcd_rpctypes_error import ErrUnhealthy
from .go_etcd_rpctypes_error import ErrUserAlreadyExist
from .go_etcd_rpctypes_error import ErrUserEmpty
from .go_etcd_rpctypes_error import ErrUserNotFound
from .go_etcd_rpctypes_error import ErrValueProvided
from .go_etcd_rpctypes_error import Etcd3Exception

__all__ = ['Etcd3Exception', 'get_client_error', 'Etcd3StreamError']

__all__ += [
    'ErrEmptyKey',
    'ErrKeyNotFound',
    'ErrValueProvided',
    'ErrLeaseProvided',
    'ErrTooManyOps',
    'ErrDuplicateKey',
    'ErrCompacted',
    'ErrFutureRev',
    'ErrNoSpace',
    'ErrLeaseNotFound',
    'ErrLeaseExist',
    'ErrLeaseTTLTooLarge',
    'ErrMemberExist',
    'ErrPeerURLExist',
    'ErrMemberNotEnoughStarted',
    'ErrMemberBadURLs',
    'ErrMemberNotFound',
    'ErrRequestTooLarge',
    'ErrTooManyRequests',
    'ErrRootUserNotExist',
    'ErrRootRoleNotExist',
    'ErrUserAlreadyExist',
    'ErrUserEmpty',
    'ErrUserNotFound',
    'ErrRoleAlreadyExist',
    'ErrRoleNotFound',
    'ErrAuthFailed',
    'ErrPermissionDenied',
    'ErrRoleNotGranted',
    'ErrPermissionNotGranted',
    'ErrAuthNotEnabled',
    'ErrInvalidAuthToken',
    'ErrInvalidAuthMgmt',
    'ErrNoLeader',
    'ErrNotLeader',
    'ErrNotCapable',
    'ErrStopped',
    'ErrTimeout',
    'ErrTimeoutDueToLeaderFail',
    'ErrTimeoutDueToConnectionLost',
    'ErrUnhealthy',
    'ErrCorrupt'
]
