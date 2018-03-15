# Models generated from rpc.swagger.json, do not edit
# flake8: noqa
import enum


class AlarmRequestAlarmAction(enum.Enum):
    """
    ref: #/definitions/AlarmRequestAlarmAction

    default: GET
    """
    GET = 'GET'
    ACTIVATE = 'ACTIVATE'
    DEACTIVATE = 'DEACTIVATE'


class CompareCompareResult(enum.Enum):
    """
    ref: #/definitions/CompareCompareResult

    default: EQUAL
    """
    EQUAL = 'EQUAL'
    GREATER = 'GREATER'
    LESS = 'LESS'
    NOT_EQUAL = 'NOT_EQUAL'


class CompareCompareTarget(enum.Enum):
    """
    ref: #/definitions/CompareCompareTarget

    default: VERSION
    """
    VERSION = 'VERSION'
    CREATE = 'CREATE'
    MOD = 'MOD'
    VALUE = 'VALUE'


class EventEventType(enum.Enum):
    """
    ref: #/definitions/EventEventType

    default: PUT
    """
    PUT = 'PUT'
    DELETE = 'DELETE'


class RangeRequestSortOrder(enum.Enum):
    """
    ref: #/definitions/RangeRequestSortOrder

    default: NONE
    """
    NONE = 'NONE'
    ASCEND = 'ASCEND'
    DESCEND = 'DESCEND'


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


class WatchCreateRequestFilterType(enum.Enum):
    """
    ref: #/definitions/WatchCreateRequestFilterType

    default: NOPUT
    """
    NOPUT = 'NOPUT'
    NODELETE = 'NODELETE'


class authpbPermissionType(enum.Enum):
    """
    ref: #/definitions/authpbPermissionType

    default: READ
    """
    READ = 'READ'
    WRITE = 'WRITE'
    READWRITE = 'READWRITE'


class etcdserverpbAlarmType(enum.Enum):
    """
    ref: #/definitions/etcdserverpbAlarmType

    default: NONE
    """
    NONE = 'NONE'
    NOSPACE = 'NOSPACE'


__all__ = [
    'AlarmRequestAlarmAction',
    'CompareCompareResult',
    'CompareCompareTarget',
    'EventEventType',
    'RangeRequestSortOrder',
    'RangeRequestSortTarget',
    'WatchCreateRequestFilterType',
    'authpbPermissionType',
    'etcdserverpbAlarmType',
]
