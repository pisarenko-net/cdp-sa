import json
import logging
import time

from .daemons import CdpDaemon
from .message_bus import Sender
from hifi_appliance.message_bus import command as channel_command


logger = logging.getLogger(__name__)


class RemoteControl(CdpDaemon):
    def __init__(self, daemon_config, debug=False):
        super(RemoteControl, self).__init__(daemon_config, debug)

    def setup_postfork(self):
        self.command_sender = Sender(
            channel_command,
            io_loop=self.io_loop
        )

    def run(self):
        # for i in range(30):
        #     self.io_loop.add_timeout(time.time() + i, self.send_current_state)

        self.io_loop.start()
