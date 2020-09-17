import threading
import time

from . import db as track_db
from .daemons import Daemon
from .message_bus import Receiver
from .message_bus import Sender
from .message_bus import command_playback as command_queue
from .message_bus import error as topic_error
from .message_bus import state as topic_state


STATE_INIT = 'PLAYBACK_INIT'
STATE_NO_DISC = 'PLAYBACK_NO_DISC'
STATE_ANALYZING = 'PLAYBACK_ANALYZING'
STATE_UNKNOWN_DISC = 'PLAYBACK_UNKNOWN_DISC'
STATE_STOPPED = 'PLAYBACK_STOPPED'
STATE_PLAYING = 'PLAYBACK_PLAYING'
STATE_PAUSED = 'PLAYBACK_PAUSED'
STATE_WAITING_FOR_DATA = 'PLAYBACK_WAITING_FOR_DATA'


class Playback(Daemon):
    def __init__(self, daemon_config, debug=False):
        self.state = STATE_INIT
        super(Playback, self).__init__(daemon_config, debug)
        self.db = track_db

    def setup_postfork(self):
        self.state_sender = Sender(
            topic_state,
            name='playback',
            io_loop=self.io_loop
        )
        self.error_sender = Sender(
            topic_error,
            name='playback',
            io_loop=self.io_loop
        )
        self.setup_command_receiver()

    def setup_command_receiver(self):
        callbacks = {}
        for name in dir(self):
            if name.startswith('command_'):
                func = getattr(self, name)
                if callable(func):
                    callbacks[name[8:]] = (
                        lambda receiver, msg, func2 = func: self.handle_command(msg, func2)
                    )

        self.command_receiver = Receiver(
            command_queue,
            io_loop = self.io_loop,
            callbacks = callbacks,
            fallback = self.handle_unknown_command
        )

    def handle_command(self, args, command_function):
        print('handling command')
        command = args[0]
        arguments = args[1:]
        result = command_function(arguments)
        return ('result', 'OK')

    def handle_unknown_command(self, receiver, msg_parts):
        print('unknown command received')
        return ('error', 'unknown command: {0}'.format(msg_parts))

    def command_disc(self, args):
        """Triggered by OS when new Audio CD inserted."""
        print('command DISC received')
        self.state_sender.send('playback', 'something is happening here')
        return 'test'

    def run(self):
        self.state = STATE_NO_DISC
        # TODO: check if there's a CD (CD player turned on with CD inside)

        # message_bus_thread = threading.Thread(
        #     target=self._generate_messages,
        #     name='message generator'
        # )
        # message_bus_thread.daemon = True
        # message_bus_thread.start()

        # for i in range(30):
        #     self.io_loop.add_timeout(time.time() + i, self.force_state_update)

        self.io_loop.start()

    # def _generate_messages(self):
    #     while True:
    #         print('Sending message')
    #         self.state_sender.send('playback', 'something is happening here')
    #         time.sleep(5)
