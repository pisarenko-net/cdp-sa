import threading
import time

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


class Playback(Daemon):
    def __init__(self, daemon_config, debug=False):
        self.db = track_db

        self.local_meta = LocalMeta()
        self.remote_meta = RemoteMeta()

        self.audio = MiniaudioSink(
            track_changed_callback = self.on_audio_track_changed, 
            need_data_callback = self.on_audio_buffer_low,
            playback_stopped_callback = self.on_audio_stopped,
            frame_played_callback = self.on_audio_frame
        )

        self.state_machine = create_player(
            read_disc_id,
            self.db.has_disc,
            self.get_known_disc,
            self.get_new_disc,
            self.start_audio,
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
            queue_command,
            io_loop = self.io_loop,
            callbacks = callbacks,
            fallback = self.handle_unknown_command
        )

    def get_known_disc(self, disc_id):
        track_list = self.db.get_track_list(disc_id)
        disc_meta = self.local_meta.query(disc_id, track_list)
        return (track_list, disc_meta)

    def get_new_disc(self, disc_id):
        disc_meta = self.remote_meta.query(disc_id)
        if not disc_meta:
            disc_meta = read_disc_meta(disc_id)
        return ([], disc_meta)

    def on_audio_buffer_low(self):
        pass

    def on_audio_track_changed(self):
        # TODO: call machine playing()
        pass

    def on_audio_stopped(self):
        # TODO: call machine, STOP
        # careful not create a cycle here
        pass

    def on_audio_frame(self):
        # TODO: call machine playing(), increase frame counter
        pass

    def on_player_state_change(self):
        pass

    def start_audio(self, track_file_name):
        self.audio.play_now(track_file_name)

    def stop_audio(self):
        self.audio.stop()

    def pause_audio(self):
        self.audio.pause()

    def resume_audio(self):
        self.audio.resume()

    def handle_command(self, args, command_function):
        print('handling command')
        command = args[0]
        arguments = args[1:]
        result = command_function(arguments)

    def handle_unknown_command(self, receiver, msg_parts):
        print('unknown command received')
        return ('error', 'unknown command: {0}'.format(msg_parts))

    def command_disc(self, args):
        """Triggered by OS when new Audio CD inserted."""
        print('command DISC received')

        self.state_machine.read_disc()
        self.state_machine.check_disc()
        self.state_machine.query_disc()
        self.state_machine.play()

    def run(self):
        self.state_machine.init()

        # for i in range(30):
        #     self.io_loop.add_timeout(time.time() + i, self.force_state_update)

        self.io_loop.start()
