import json
import sys

from .constants import SAMPLE_RATE
from .daemons import CdpDaemon
from .message_bus import Receiver
from .message_bus import state as channel_state
from .state import PlayerStates


class Display(CdpDaemon):
    def __init__(self, daemon_config, debug=False):
        super(Display, self).__init__(daemon_config, debug)

    def setup_postfork(self):
        self.state_receiver = Receiver(
            channel_state,
            name='display',
            io_loop=self.io_loop,
            callbacks={
                'playback': lambda receiver, message: self.on_state(message)
            }
        )

        self.last_known_track = None
        self.last_elapsed_seconds = None

    def on_state(self, message):
        state_dict = json.loads(message[1])
        player_state = PlayerStates(state_dict['state'])

        display_function = getattr(self, 'display_cd_%s' % player_state.name.lower())
        display_function(state_dict)

    def run(self):
        self.io_loop.start()

    #
    # CD State display functions

    def display_cd_no_disc(self, state_dict):
        print('NO DISC')
        self.last_known_track = None
        self.current_elapsed_seconds = None

    def display_cd_unknown_disc(self, state_dict):
        print('UNSUPPORTED DISC')

    def display_cd_stopped(self, state_dict):
        total_tracks = len(state_dict['track_list'])
        current_track = state_dict['current_track']
        total_seconds = state_dict['disc_meta']['tracks'][current_track]['duration'] / SAMPLE_RATE * 2
        track_duration_readable = self._get_readable_duration(total_seconds)
        print('⏹ %d/%d %s' % (current_track, total_tracks, track_duration_readable))

    def _get_readable_duration(self, total_seconds):
        minutes = total_seconds / 60
        seconds = total_seconds % 60
        return '%02d:%02d' % (minutes, seconds)

    def display_cd_playing(self, state_dict):
        current_track = state_dict['current_track']
        current_elapsed_seconds = state_dict['current_frame'] // SAMPLE_RATE

        if current_track != self.last_known_track:
            self.last_known_track = current_track
        elif current_elapsed_seconds == self.last_elapsed_seconds:
            return

        self.last_elapsed_seconds = current_elapsed_seconds
        total_tracks = len(state_dict['track_list'])
        elapsed_readable = self._get_readable_duration(current_elapsed_seconds)
        print('▶ %d/%d %s' % (current_track, total_tracks, elapsed_readable))

    def display_cd_paused(self, state_dict):
        current_track = state_dict['current_track']
        current_elapsed_seconds = state_dict['current_frame'] // SAMPLE_RATE
        total_tracks = len(state_dict['track_list'])
        elapsed_readable = self._get_readable_duration(current_elapsed_seconds)
        print('⏸ %d/%d %s' % (current_track, total_tracks, elapsed_readable))

    def display_cd_waiting_for_data(self, state_dict):
        total_tracks = len(state_dict['track_list'])
        current_track = state_dict['current_track']
        total_seconds = state_dict['disc_meta']['tracks'][current_track]['duration'] / SAMPLE_RATE * 2
        track_duration_readable = self._get_readable_duration(total_seconds)
        print('▶ %d/%d %s\nWAITING FOR RIP' % (current_track, total_tracks, track_duration_readable))
