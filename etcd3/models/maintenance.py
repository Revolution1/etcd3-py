import enum


class AlarmAction(enum.Enum):
    GET = 'GET'
    ACTIVATE = 'ACTIVATE'
    DEACTIVATE = 'DEACTIVATE'


class AlarmType(enum.Enum):
    NONE = "NONE"
    NOSPACE = "NOSPACE"
