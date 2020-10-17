from collections import namedtuple
import getpass

from hifi_appliance.daemons import CdpDaemon
from hifi_appliance.message_bus import Receiver
from hifi_appliance.message_bus import state as channel_state
from hifi_appliance.message_bus import error as channel_error
from hifi_appliance.message_bus import command as channel_command
from hifi_appliance.message_bus import command_playback as channel_command_playback


class MessageMonitor(CdpDaemon):
    def __init__(self, daemon_config, debug = False):
        super(MessageMonitor, self).__init__(daemon_config, debug)

    def create_callback(self, name):
        return lambda receiver, message: print('Received in %s: %s' % (name, message))

    def setup_postfork(self):
        self.state_receiver = Receiver(
            channel_state,
            name='monitor',
            io_loop=self.io_loop,
            callbacks={
                'playback': None,
                'ripping': None
            },
            fallback=self.create_callback('state')
        )

        self.error_receiver = Receiver(
            channel_error,
            name='monitor',
            io_loop=self.io_loop,
            callbacks={
                'playback': None,
                'ripping': None
            },
            fallback=self.create_callback('error')
        )

        # these below can be uncommented when there's no other receiver

        # self.command_receiver = Receiver(
        #     channel_command,
        #     io_loop=self.io_loop,
        #     callbacks={},
        #     fallback=self.create_callback('command')
        # )

        # self.playback_receiver = Receiver(
        #     channel_command_playback,
        #     io_loop=self.io_loop,
        #     callbacks={},
        #     fallback=self.create_callback('command_playback')
        # )

    def run(self):
        self.io_loop.start()


if __name__ == '__main__':
    config = namedtuple(
        'DaemonConfig',
        ['user', 'group', 'initgroups', 'pid_file', 'log_file']
    )
    config.user = getpass.getuser()
    config.group = getpass.getuser()

    MessageMonitor(config, debug=True)
