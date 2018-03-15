from .base import BaseAPI
from ..models import AlarmRequestAlarmAction
from ..models import etcdserverpbAlarmType


class MaintenanceAPI(BaseAPI):
    def alarm(self, memberID, action=AlarmRequestAlarmAction.GET, alarm=etcdserverpbAlarmType.NONE):
        """
        Alarm activates, deactivates, and queries alarms regarding cluster health.

        :type action: AlarmRequestAlarmAction
        :param action: action is the kind of alarm request to issue. The action
            may GET alarm statuses, ACTIVATE an alarm, or DEACTIVATE a
            raised alarm.
        :type memberID: int
        :param memberID: memberID is the ID of the member associated with the alarm. If memberID is 0, the
            alarm request covers all members.
        :type alarm: etcdserverpbAlarmType
        :param alarm: alarm is the type of alarm to consider for this request.
        """
        method = '/v3alpha/maintenance/alarm'
        data = {
            "action": action,
            "memberID": memberID,
            "alarm": alarm
        }
        return self.call_rpc(method, data=data)

    def alarm_get(self, memberID, alarm):
        """
        Queries alarms regarding cluster health.

        :type memberID: int
        :param memberID: memberID is the ID of the member associated with the alarm. If memberID is 0, the
            alarm request covers all members.
        :type alarm: etcdserverpbAlarmType
        :param alarm: alarm is the type of alarm to consider for this request.
        """
        return self.alarm(memberID, AlarmRequestAlarmAction.GET, alarm)

    def alarm_activate(self, memberID, alarm):
        """
        Activates alarms regarding cluster health.

        :type memberID: int
        :param memberID: memberID is the ID of the member associated with the alarm. If memberID is 0, the
            alarm request covers all members.
        :type alarm: etcdserverpbAlarmType
        :param alarm: alarm is the type of alarm to consider for this request.
        """
        return self.alarm(memberID, AlarmRequestAlarmAction.ACTIVATE, alarm)

    def alarm_deactivate(self, memberID, alarm):
        """
        Deactivates alarms regarding cluster health.

        :type memberID: int
        :param memberID: memberID is the ID of the member associated with the alarm. If memberID is 0, the
            alarm request covers all members.
        :type alarm: etcdserverpbAlarmType
        :param alarm: alarm is the type of alarm to consider for this request.
        """
        return self.alarm(memberID, AlarmRequestAlarmAction.DEACTIVATE, alarm)

    def defragment(self):
        """
        Defragment defragments a member's backend database to recover storage space.
        """
        method = '/v3alpha/maintenance/defragment'
        data = {}
        return self.call_rpc(method, data=data)

    def hash(self):
        """
        Hash returns the hash of the local KV state for consistency checking purpose.
        This is designed for testing; do not use this in production when there
        are ongoing transactions.
        """
        method = '/v3alpha/maintenance/hash'
        data = {}
        return self.call_rpc(method, data=data)

    def snapshot(self):
        """
        Snapshot sends a snapshot of the entire backend from a member over a stream to a client.
        """
        method = '/v3alpha/maintenance/snapshot'
        data = {}
        return self.call_rpc(method, data=data, stream=True)

    def status(self):
        """
        Status gets the status of the member.
        """
        method = '/v3alpha/maintenance/status'
        data = {}
        return self.call_rpc(method, data=data)
