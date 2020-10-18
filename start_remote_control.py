from collections import namedtuple

from hifi_appliance.remote_control import RemoteControl
from hifi_appliance.config import DAEMON_GROUP
from hifi_appliance.config import DAEMON_USER
from hifi_appliance.config import DEBUG
from hifi_appliance.config import LOG_FILE_REMOTE_CONTROL
from hifi_appliance.config import PID_FILE_REMOTE_CONTROL


daemon_config = namedtuple(
    'DaemonConfig',
    ['user', 'group', 'initgroups', 'pid_file', 'log_file']
)
daemon_config.user = DAEMON_USER
daemon_config.group = DAEMON_GROUP
daemon_config.initgroups = False
daemon_config.pid_file = PID_FILE_REMOTE_CONTROL
daemon_config.log_file = LOG_FILE_REMOTE_CONTROL


remote_control = RemoteControl(daemon_config, debug=DEBUG)
