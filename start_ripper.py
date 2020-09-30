from collections import namedtuple

from hifi_appliance.ripping import Ripping


daemon_config = namedtuple(
    'DaemonConfig',
    ['user', 'group', 'initgroups', 'pid_file', 'log_file']
)
daemon_config.user = 'sergey'
daemon_config.group = 'sergey'
daemon_config.initgroups = False
daemon_config.pid_file = '/home/sergey/playback.pid'
daemon_config.log_file = '/home/sergey/playback.log'


ripping = Ripping(daemon_config, debug=True)
