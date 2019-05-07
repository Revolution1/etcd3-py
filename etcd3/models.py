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
    ACTIVATE = 'ACTIVATE'
    DEACTIVATE = 'DEACTIVATE'
    GET = 'GET'


class authpbPermissionType(EtcdModel, enum.Enum):
    """
    ref: #/definitions/authpbPermissionType

    default: READ
    """
    READ = 'READ'
    READWRITE = 'READWRITE'
    WRITE = 'WRITE'


class EventEventType(EtcdModel, enum.Enum):
    """
    ref: #/definitions/EventEventType

    default: PUT
    """
    DELETE = 'DELETE'
    PUT = 'PUT'


class RangeRequestSortTarget(EtcdModel, enum.Enum):
    """
    ref: #/definitions/RangeRequestSortTarget

    default: KEY
    """
    CREATE = 'CREATE'
    KEY = 'KEY'
    MOD = 'MOD'
    VALUE = 'VALUE'
    VERSION = 'VERSION'


class etcdserverpbAlarmType(EtcdModel, enum.Enum):
    """
    ref: #/definitions/etcdserverpbAlarmType

    default: NONE
    """
    NONE = 'NONE'
    NOSPACE = 'NOSPACE'


class CompareCompareResult(EtcdModel, enum.Enum):
    """
    ref: #/definitions/CompareCompareResult

    default: EQUAL
    """
    EQUAL = 'EQUAL'
    GREATER = 'GREATER'
    LESS = 'LESS'
    NOT_EQUAL = 'NOT_EQUAL'


class RangeRequestSortOrder(EtcdModel, enum.Enum):
    """
    ref: #/definitions/RangeRequestSortOrder

    default: NONE
    """
    ASCEND = 'ASCEND'
    DESCEND = 'DESCEND'
    NONE = 'NONE'


class CompareCompareTarget(EtcdModel, enum.Enum):
    """
    ref: #/definitions/CompareCompareTarget

    default: VERSION
    """
    CREATE = 'CREATE'
    MOD = 'MOD'
    VALUE = 'VALUE'
    VERSION = 'VERSION'


class WatchCreateRequestFilterType(EtcdModel, enum.Enum):
    """
    ref: #/definitions/WatchCreateRequestFilterType

    default: NOPUT
    """
    NODELETE = 'NODELETE'
    NOPUT = 'NOPUT'


name_to_model = {
    'AlarmRequestAlarmAction': AlarmRequestAlarmAction,
    'authpbPermissionType': authpbPermissionType,
    'EventEventType': EventEventType,
    'RangeRequestSortTarget': RangeRequestSortTarget,
    'etcdserverpbAlarmType': etcdserverpbAlarmType,
    'CompareCompareResult': CompareCompareResult,
    'RangeRequestSortOrder': RangeRequestSortOrder,
    'CompareCompareTarget': CompareCompareTarget,
    'WatchCreateRequestFilterType': WatchCreateRequestFilterType,
}
__all__ = [
    'AlarmRequestAlarmAction',
    'authpbPermissionType',
    'EventEventType',
    'RangeRequestSortTarget',
    'etcdserverpbAlarmType',
    'CompareCompareResult',
    'RangeRequestSortOrder',
    'CompareCompareTarget',
    'WatchCreateRequestFilterType',
    'name_to_model',
    'EtcdModel',
]
