from collections import namedtuple

from hifi_appliance.playback import Player
from hifi_appliance.display import Display
#from hifi_appliance import db

daemon_config = namedtuple(
    'DaemonConfig',
    ['user', 'group', 'initgroups', 'pid_file', 'log_file']
)
daemon_config.user = 'sergey'
daemon_config.group = 'sergey'
daemon_config.initgroups = False
daemon_config.pid_file = '/home/sergey/player.pid'
daemon_config.log_file = '/home/sergey/player.log'

#player = Player(daemon_config, debug=False)
#display = Display(daemon_config, debug=True)
