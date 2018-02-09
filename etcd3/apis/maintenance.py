from . import BaseAPI
from ..models import AlarmAction


class MaintenanceAPI(BaseAPI):

    def alarm_request(self, alarm_action, member_id, alarm_type):
        """
        Alarm activates, deactivates, and queries alarms regarding cluster health.
        :param alarm_action: AlarmAction
        :param member_id: int
        :param alarm_type:
        """
        method = '/v3alpha/maintenance/alarm'
        data = {
            "action": alarm_action,
            "memberID": member_id,
            "alarm": alarm_type
        }
        return self.call_rpc(method, data=data)

    def get_alarm(self, member_id, alarm_type):
        return self.alarm_request(AlarmAction.GET, member_id, alarm_type)

    def activate_alarm(self, member_id, alarm_type):
        return self.alarm_request(AlarmAction.ACTIVATE, member_id, alarm_type)

    def deactivate_alarm(self, member_id, alarm_type):
        return self.alarm_request(AlarmAction.DEACTIVATE, member_id, alarm_type)

    def defragment(self):
        """
        Defragment defragments a member's backend database to recover storage space.
        """
        method = '/v3alpha/maintenance/defragment'
        return self.call_rpc(method)

    def hash(self):
        """
        Hash returns the hash of the local KV state for consistency checking purpose.
        This is designed for testing; do not use this in production when there are ongoing transactions.
        """
        method = '/v3alpha/maintenance/hash'
        return self.call_rpc(method)

    def snapshot(self):
        """
        Snapshot sends a snapshot of the entire backend from a member over a stream to a client.
        """
        method = '/v3alpha/maintenance/snapshot'
        return self.call_rpc(method)

    def status(self):
        """
        Status gets the status of the member.
        """
        method = '/v3alpha/maintenance/status'
        return self.call_rpc(method)
