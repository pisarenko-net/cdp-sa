import json
import logging
import threading
import time

import transitions

from . import db as track_db
from .audio import MiniaudioSink
from .daemons import Daemon
from .disc import read_disc_id
from .disc import read_disc_meta
from .message_bus import Receiver
from .message_bus import Sender
from .message_bus import command_playback as queue_command
from .message_bus import error as topic_error
from .message_bus import state as topic_state
from .meta import LocalMeta
from .meta import RemoteMeta
from .state import create_player


logger = logging.getLogger(__name__)


class Playback(Daemon):
    def __init__(self, daemon_config, debug=False):
        self.db = track_db

        self.local_meta = LocalMeta()
        self.remote_meta = RemoteMeta()

        self.audio = MiniaudioSink(
            track_changed_callback = self.on_audio_track_changed, 
            need_data_callback = self.on_audio_buffer_low,
            playback_stopped_callback = self.on_audio_stopped,
            frames_played_callback = self.on_audio_frames
        )

        self.state_machine = create_player(
            read_disc_id,
            self.db.has_disc,
            self.get_known_disc,
            self.get_new_disc,
            self.audio.play_now,
            self.audio.play_next,
            self.audio.stop,
            self.audio.pause,
            self.audio.resume,
            self.on_player_state_change
        )

        super(Playback, self).__init__(daemon_config, debug)

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

        self.state_machine.init()

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
            queue_command,
            io_loop = self.io_loop,
            callbacks = callbacks,
            fallback = self.handle_unknown_command
        )

    def get_known_disc(self, disc_id):
        logger.info('Disc already indexed: reading meta from file system')
        track_list = self.db.get_track_list(disc_id)
        disc_meta = self.local_meta.query(disc_id, track_list)
        return (track_list, disc_meta)

    def get_new_disc(self, disc_id):
        logger.info('New disc: reading meta online or from the disc itself')
        disc_meta = self.remote_meta.query(disc_id)
        if not disc_meta:
            disc_meta = read_disc_meta(disc_id)
        return ([], disc_meta)

    def on_audio_buffer_low(self):
        self.state_machine.buffer()

    def on_audio_track_changed(self):
        self.state_machine.playing(0, track_changed=True)

    def on_audio_stopped(self):
        # TODO: call machine, STOP
        # careful not create a cycle here
        pass

    def on_audio_frames(self, frames):
        self.state_machine.playing(frames)

    def on_player_state_change(self):
        self.send_current_state()

    def send_current_state(self):
        self.state_sender.send(json.dumps(self.state_machine.get_full_state()))

    def handle_command(self, args, command_function):
        command = args[0]
        arguments = args[1:]

        logger.debug('Received command %s with arguments %s', command, arguments)

        try:
            result = command_function(arguments)
        except transitions.core.MachineError:
            logger.exception('State machine refused transition')

    def handle_unknown_command(self, receiver, msg_parts):
        logger.error('Unknown command received %s', msg_parts)

    def command_disc(self, args):
        """Triggered by OS when new Audio CD inserted."""
        self.state_machine.read_disc()
        self.state_machine.check_disc()
        self.state_machine.query_disc()
        self.state_machine.play()

    def command_play(self, args):
        self.state_machine.play()

    def command_stop(self, args):
        self.state_machine.stop()

    def command_pause(self, args):
        self.state_machine.pause()

    def command_next(self, args):
        self.state_machine.next()

    def command_prev(self, args):
        self.state_machine.prev()

    def command_state(self, arg):
        self.send_current_state()

    def command_db_rebuild(self, args):
        self.db.rebuild()

    def command_db_stat(self, args):
        print('%s discs indexed' % self.db.count())

    def run(self):
        # for i in range(30):
        #     self.io_loop.add_timeout(time.time() + i, self.force_state_update)

        self.io_loop.start()


# state machine decrements track number and then checks,
# what if it's invalid -- previous value is never restored
