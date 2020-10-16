import json
import logging
import time

from .audio import MiniaudioSink
from .daemons import CdpDaemon
from .message_bus import Receiver
from .message_bus import Sender
from .message_bus import command_playback as channel_command
from .message_bus import state as channel_state
from .state import create_player
from .state import PlayerStates


logger = logging.getLogger(__name__)


class PlaybackCommand(object):
    UNKNOWN_DISC = 'unknown_disc'
    START = 'start'
    PLAY = 'play'
    STOP = 'stop'
    PAUSE = 'pause'
    NEXT = 'next'
    PREV = 'prev'
    EJECT = 'eject'
    STATE = 'state'


class Playback(CdpDaemon):
    def __init__(self, daemon_config, debug=False):
        self.audio = None

        self.state_machine = create_player(
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
            channel_state,
            name='playback',
            io_loop=self.io_loop
        )

        self.state_receiver = Receiver(
            channel_state,
            name='playback',
            io_loop=self.io_loop,
            callbacks={
                'ripping': self.on_ripping_state
            }
        )

        self.command_receiver = self.setup_command_receiver(channel_command)

        self.state_machine.init()

    def run(self):
        # for i in range(30):
        #     self.io_loop.add_timeout(time.time() + i, self.send_current_state)

        self.io_loop.start()

    #
    # Interface between state machine and audio

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
        if self.audio:
            self.audio.pause()
            self.audio.release()
            self.audio = None

    def send_current_state(self):
        self.state_sender.send(json.dumps(self.state_machine.get_full_state()))

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
    # Ripper updates

    def on_ripping_state(self, receiver, args):
        ripping_state = json.loads(args[1])
        self.state_machine.ripper_update(ripping_state['track_list'])

        if self.state_machine.state == PlayerStates.WAITING_FOR_DATA:
            self.state_machine.play()

    #
    # Control commands

    def command_unknown_disc(self, args):
        self.state_machine.unknown_disc()

    def command_start(self, args):
        track_list = json.loads(args[0])
        disc_meta = json.loads(args[1])
        self.state_machine.start(track_list, disc_meta)

    def command_eject(self, args):
        self.state_machine.eject()

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

# test case: next called when data is not available yet
