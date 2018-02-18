# Models generated from rpc.swagger.json, do not edit
import enum


class AlarmRequestAlarmAction(enum.Enum):
    """
    ref: #/definitions/AlarmRequestAlarmAction
    default: GET
    """
    GET = 'GET'
    ACTIVATE = 'ACTIVATE'
    DEACTIVATE = 'DEACTIVATE'


class EventEventType(enum.Enum):
    """
    ref: #/definitions/EventEventType
    default: PUT
    """
    PUT = 'PUT'
    DELETE = 'DELETE'


class RangeRequestSortTarget(enum.Enum):
    """
    ref: #/definitions/RangeRequestSortTarget
    default: KEY
    """
    KEY = 'KEY'
    VERSION = 'VERSION'
    CREATE = 'CREATE'
    MOD = 'MOD'
    VALUE = 'VALUE'


class CompareCompareTarget(enum.Enum):
    """
    ref: #/definitions/CompareCompareTarget
    default: VERSION
    """
    VERSION = 'VERSION'
    CREATE = 'CREATE'
    MOD = 'MOD'
    VALUE = 'VALUE'


class authpbPermissionType(enum.Enum):
    """
    ref: #/definitions/authpbPermissionType
    default: READ
    """
    READ = 'READ'
    WRITE = 'WRITE'
    READWRITE = 'READWRITE'


class CompareCompareResult(enum.Enum):
    """
    ref: #/definitions/CompareCompareResult
    default: EQUAL
    """
    EQUAL = 'EQUAL'
    GREATER = 'GREATER'
    LESS = 'LESS'
    NOT_EQUAL = 'NOT_EQUAL'


class RangeRequestSortOrder(enum.Enum):
    """
    ref: #/definitions/RangeRequestSortOrder
    default: NONE
    """
    NONE = 'NONE'
    ASCEND = 'ASCEND'
    DESCEND = 'DESCEND'


class etcdserverpbAlarmType(enum.Enum):
    """
    ref: #/definitions/etcdserverpbAlarmType
    default: NONE
    """
    NONE = 'NONE'
    NOSPACE = 'NOSPACE'


class WatchCreateRequestFilterType(enum.Enum):
    """
    ref: #/definitions/WatchCreateRequestFilterType
    default: NOPUT
    """
    NOPUT = 'NOPUT'
    NODELETE = 'NODELETE'


__all__ = [
    'AlarmRequestAlarmAction',
    'EventEventType',
    'RangeRequestSortTarget',
    'CompareCompareTarget',
    'authpbPermissionType',
    'CompareCompareResult',
    'RangeRequestSortOrder',
    'etcdserverpbAlarmType',
    'WatchCreateRequestFilterType',
]
