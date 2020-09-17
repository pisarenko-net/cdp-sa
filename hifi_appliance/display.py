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
                'playback': lambda receiver, message: print(message)
            }
        )

    def run(self):
        self.io_loop.start()
