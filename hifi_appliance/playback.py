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
from .message_bus import setup_command_receiver
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

        self.audio = None

        self.state_machine = create_player(
            read_disc_id,
            self.db.has_disc,
            self.get_known_disc,
            self.get_new_disc,
            self.create_audio,
            self.buffer_track,
            self.stop_audio,
            self.pause_audio,
            self.resume_audio,
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
        self.command_receiver = setup_command_receiver(self, queue_command)

        self.state_machine.init()

    def run(self):
        for i in range(30):
            self.io_loop.add_timeout(time.time() + i, self.send_current_state)

        self.io_loop.start()

    #
    # Interface for state machine

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

    def create_audio(self):
        if self.audio:
            logger.critical('New audio device requested while old one still exists')

        self.audio = MiniaudioSink(
            playback_stopped_callback = self.on_audio_stopped,
            frames_played_callback = self.on_audio_frames
        )

    def buffer_track(self, track_file_name):
        return self.audio.buffer_track(track_file_name)

    def resume_audio(self):
        self.audio.resume()

    def pause_audio(self):
        self.audio.pause()

    def stop_audio(self):
        logger.debug('Requested to release audio device')
        self.audio.pause()
        self.audio.release()
        self.audio = None

    def send_current_state(self):
        self.state_sender.send(json.dumps(self.state_machine.get_full_state()))

    #
    # Receiving commands

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

    #
    # Audio events

    def on_audio_stopped(self):
        logger.debug('Audio ran out of frames, releasing audio and stopping state machine')
        self.audio = None
        self.state_machine.finish()

    def on_audio_frames(self, frames):
        self.state_machine.playing(frames)

    #
    # State machine events

    def on_player_state_change(self):
        self.send_current_state()

    #
    # Control commands

    def command_disc(self, args):
        """Triggered by OS when new Audio CD inserted."""
        self.state_machine.read_disc()
        self.state_machine.check_disc()
        self.state_machine.query_disc()

    #
    # Playback commands

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

    #
    # Debug commands

    def command_state(self, arg):
        self.send_current_state()

    def command_db_rebuild(self, args):
        self.db.rebuild()

    def command_db_stat(self, args):
        print('%s discs indexed' % self.db.count())
