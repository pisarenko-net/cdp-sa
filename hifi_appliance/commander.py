import json
import logging
import time

from . import db as track_db
from .daemons import CdpDaemon
from .disc import read_disc_id
from .disc import read_disc_meta
from .message_bus import Receiver
from .message_bus import Sender
from .message_bus import command as channel_command
from .message_bus import command_playback as channel_playback_command
from .message_bus import command_ripping as channel_ripping_command
from .message_bus import state as channel_state
from .meta import LocalMeta
from .meta import RemoteMeta
from .playback import PlaybackCommand
from .ripping import RippingCommand
from .state import PlayerStates
from .state import RipperStates


logger = logging.getLogger(__name__)


class Commander(CdpDaemon):
    def __init__(self, daemon_config, debug=False):
        self.db = track_db

        self.local_meta = LocalMeta()
        self.remote_meta = RemoteMeta()

        self.playback_state = None
        self.ripping_state = None

        super(Commander, self).__init__(daemon_config, debug)

    def setup_postfork(self):
        self.state_sender = Sender(
            channel_state,
            name='commander',
            io_loop=self.io_loop
        )

        self.plyaback_state_receiver = Receiver(
            channel_state,
            name='commander',
            io_loop=self.io_loop,
            callbacks={
                'playback': self.update_playback_state,
                'ripping': self.update_ripping_state
            }
        )

        self.playback_command = Sender(
            channel_playback_command,
            io_loop=self.io_loop
        )
        self.ripper_command = Sender(
            channel_ripping_command,
            io_loop=self.io_loop
        )

        self.command_receiver = self.setup_command_receiver(channel_command)

    def run(self):
        # for i in range(30):
        #     self.io_loop.add_timeout(time.time() + i, self.send_current_state)

        self.io_loop.start()

    #
    # Receive state updates

    def update_playback_state(self, receiver, args):
        playback_state = json.loads(args[1])
        self.playback_state = PlayerStates(playback_state['state'])

    def update_ripping_state(self, receiver, args):
        ripping_state = json.loads(args[1])
        self.ripping_state = RipperStates(ripping_state['state'])

    #
    # Disc look-up

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

    #
    # Control commands

    def command_disc(self, args):
        """Triggered by OS when new Audio CD inserted."""

        disc_id = read_disc_id()

        if not disc_id:
            self.playback_command.send(PlaybackCommand.UNKNOWN_DISC)
            return

        disc_query_func = self.get_known_disc if self.db.has_disc(disc_id) else self.get_new_disc
        (track_list, disc_meta) = disc_query_func(disc_id)

        if not disc_meta:
            self.playback_command.send(PlaybackCommand.UNKNOWN_DISC)
            return

        self.playback_command.send(
            PlaybackCommand.START,
            json.dumps(track_list),
            json.dumps(disc_meta)
        )

        self.ripper_command.send(RippingCommand.START, json.dumps(disc_meta))

    def command_eject(self, args):
        self.playback_command.send(PlaybackCommand.EJECT)

    #
    # Playback commands

    def command_play(self, args):
        self.playback_command.send(PlaybackCommand.PLAY)

    def command_stop(self, args):
        self.playback_command.send(PlaybackCommand.STOP)

    def command_pause(self, args):
        self.playback_command.send(PlaybackCommand.PAUSE)

    def command_next(self, args):
        self.playback_command.send(PlaybackCommand.NEXT)

    def command_prev(self, args):
        self.playback_command.send(PlaybackCommand.PREV)

    #
    # Debug commands

    def command_db_rebuild(self, args):
        self.db.rebuild()

    def command_db_stat(self, args):
        print('%s discs indexed' % self.db.count())
