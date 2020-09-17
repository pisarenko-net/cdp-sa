import threading
import time

from .daemons import Daemon
from .message_bus import Receiver
from .message_bus import Sender
from .message_bus import error as topic_error
from .message_bus import state as topic_state


class Player(Daemon):
    def __init__(self, daemon_config, debug=False):
        super(Player, self).__init__(daemon_config, debug)

    def setup_postfork(self):
        self.state_sender = Sender(
            topic_state,
            name='player',
            io_loop=self.io_loop
        )
        self.error_sender = Sender(
            topic_error,
            name='player',
            io_loop=self.io_loop
        )

    def run(self):
        message_bus_thread = threading.Thread(
            target=self._generate_messages,
            name='message generator'
        )
        message_bus_thread.daemon = True
        message_bus_thread.start()

        self.io_loop.start()

    def _generate_messages(self):
        while True:
            print('Sending message')
            self.state_sender.send('playback', 'something is happening here')
            time.sleep(5)

