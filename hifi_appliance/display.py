import json
import sys

from .daemons import Daemon
from .message_bus import Receiver
from .message_bus import state as topic_state


class Display(Daemon):
    def __init__(self, daemon_config, debug=False):
        super(Display, self).__init__(daemon_config, debug)

    def setup_postfork(self):
        self.state_receiver = Receiver(
            topic_state,
            name='display',
            io_loop=self.io_loop,
            callbacks={
                'playback': lambda receiver, message: self.on_state(message)
            }
        )

    def on_state(self, message):
        state = json.loads(message[1])
        if 'current_frame' in state and 'total_frames' in state:
            sys.stdout.write('%s / %s \r' % (state['current_frame'], state['total_frames']))

    def run(self):
        self.io_loop.start()
