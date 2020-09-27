import json
import sys

from .daemons import Daemon
from .message_bus import Receiver
from .message_bus import state as channel_state
from .state import PlayerStates


class Display(Daemon):
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

    def on_state(self, message):
        state = json.loads(message[1])

        sys.stdout.write(
            '%s %s %s %s %s \r' % (
                PlayerStates(state['state']),
                state['next_track_frames'],
                state['current_track'],
                state['current_frame'],
                state['total_frames']
            )
        )

        # if state['current_frame'] and state['total_frames']:
        #     current_track = state['current_track']
        #     total_tracks = len(state['track_list'])
        #     track_meta = state['disc_meta']['tracks'][current_track - 1]
        #     artist = track_meta['artist']
        #     title = track_meta['title']
        #     sys.stdout.write(
        #         'Playing now [%s/%s] %s - %s %s / %s \r' % (
        #             current_track,
        #             total_tracks,
        #             artist,
        #             title,
        #             state['current_frame'],
        #             state['total_frames']
        #         )
        #     )

    def run(self):
        self.io_loop.start()
