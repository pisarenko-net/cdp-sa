import json
import logging
import threading
import time

import lirc

from .daemons import CdpDaemon
from .message_bus import Sender
from hifi_appliance.commander import CdpCommand
from hifi_appliance.message_bus import command as channel_command


logger = logging.getLogger(__name__)


REMOTE_KEY_TO_COMMAND = {
    'KEY_PLAY': CdpCommand.PLAY,
    'KEY_PAUSE': CdpCommand.PAUSE,
    'KEY_STOP': CdpCommand.STOP,
    'KEY_NEXT': CdpCommand.NEXT,
    'KEY_PREVIOUS': CdpCommand.PREV,
    'KEY_EJECTCD': CdpCommand.EJECT,
}

REMOTE_NAME = 'denon'


class RemoteControl(CdpDaemon):
    def __init__(self, daemon_config, debug=False):
        super(RemoteControl, self).__init__(daemon_config, debug)

    def setup_postfork(self):
        self.command_sender = Sender(
            channel_command,
            io_loop=self.io_loop
        )

        self.thread = threading.Thread(
            target=self.receive_lirc_commands,
            name='lirc command receiver'
        )
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        # for i in range(30):
        #     self.io_loop.add_timeout(time.time() + i, self.send_current_state)

        self.io_loop.start()


    def receive_lirc_commands(self):
        with lirc.RawConnection(None) as conn:
            while True:
                (code, seq, key, remote) = conn.readline().split(' ')
                if remote != REMOTE_NAME:
                    logging.error('Received %s key for remote "%s" but configured for "%s"' % (key, remote, REMOTE_NAME))
                    continue
                if key not in REMOTE_KEY_TO_COMMAND.keys():
                    logging.error('Received unregistered %s key' % key)
                    continue
                if seq != '00':
                    logging.debug('Ignoring repeated key press %s %s' % (key, seq))
                    continue

                self.command_sender.send(REMOTE_KEY_TO_COMMAND[key])
