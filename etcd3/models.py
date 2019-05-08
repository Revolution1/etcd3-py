# Models generated from rpc.swagger.json, do not edit
# flake8: noqa
import enum


class EtcdModel(object):
    pass


class AlarmRequestAlarmAction(EtcdModel, enum.Enum):
    """
    ref: #/definitions/AlarmRequestAlarmAction

    default: GET
    """
    GET = 'GET'
    ACTIVATE = 'ACTIVATE'
    DEACTIVATE = 'DEACTIVATE'


class CompareCompareResult(EtcdModel, enum.Enum):
    """
    ref: #/definitions/CompareCompareResult

    default: EQUAL
    """
    EQUAL = 'EQUAL'
    GREATER = 'GREATER'
    LESS = 'LESS'
    NOT_EQUAL = 'NOT_EQUAL'


class CompareCompareTarget(EtcdModel, enum.Enum):
    """
    ref: #/definitions/CompareCompareTarget

    default: VERSION
    """
    VERSION = 'VERSION'
    CREATE = 'CREATE'
    MOD = 'MOD'
    VALUE = 'VALUE'
    LEASE = 'LEASE'


class EventEventType(EtcdModel, enum.Enum):
    """
    ref: #/definitions/EventEventType

    default: PUT
    """
    PUT = 'PUT'
    DELETE = 'DELETE'


class RangeRequestSortOrder(EtcdModel, enum.Enum):
    """
    ref: #/definitions/RangeRequestSortOrder

    default: NONE
    """
    NONE = 'NONE'
    ASCEND = 'ASCEND'
    DESCEND = 'DESCEND'


class RangeRequestSortTarget(EtcdModel, enum.Enum):
    """
    ref: #/definitions/RangeRequestSortTarget

    default: KEY
    """
    KEY = 'KEY'
    VERSION = 'VERSION'
    CREATE = 'CREATE'
    MOD = 'MOD'
    VALUE = 'VALUE'


class WatchCreateRequestFilterType(EtcdModel, enum.Enum):
    """
    ref: #/definitions/WatchCreateRequestFilterType

    default: NOPUT
    """
    NOPUT = 'NOPUT'
    NODELETE = 'NODELETE'


class authpbPermissionType(EtcdModel, enum.Enum):
    """
    ref: #/definitions/authpbPermissionType

    default: READ
    """
    READ = 'READ'
    WRITE = 'WRITE'
    READWRITE = 'READWRITE'


class etcdserverpbAlarmType(EtcdModel, enum.Enum):
    """
    ref: #/definitions/etcdserverpbAlarmType

    default: NONE
    """
    NONE = 'NONE'
    NOSPACE = 'NOSPACE'
    CORRUPT = 'CORRUPT'


name_to_model = {
    'AlarmRequestAlarmAction': AlarmRequestAlarmAction,
    'CompareCompareResult': CompareCompareResult,
    'CompareCompareTarget': CompareCompareTarget,
    'EventEventType': EventEventType,
    'RangeRequestSortOrder': RangeRequestSortOrder,
    'RangeRequestSortTarget': RangeRequestSortTarget,
    'WatchCreateRequestFilterType': WatchCreateRequestFilterType,
    'authpbPermissionType': authpbPermissionType,
    'etcdserverpbAlarmType': etcdserverpbAlarmType,
}

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
    'EtcdModel',
    'name_to_model',
]
