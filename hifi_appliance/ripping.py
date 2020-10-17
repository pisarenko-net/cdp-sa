from concurrent.futures import ThreadPoolExecutor
import json
import logging
import shutil
import subprocess
import tempfile
import time

from .daemons import CdpDaemon
from .message_bus import Receiver
from .message_bus import Sender
from .message_bus import command_ripping as channel_command
from .message_bus import state as channel_state
from .meta import write_meta
from .state import create_ripper


logger = logging.getLogger(__name__)


class RippingCommand(object):
    START = 'start'
    KNOWN_DISC = 'known_disc'
    STATE = 'state'


class Ripping(CdpDaemon):
    def __init__(self, daemon_config, debug=False):
        self.state_machine = create_ripper(
            self.grab_and_convert_track,
            self.create_folder,
            write_meta,
            self.move_track,
            self.write_disc_id,
            self.on_state_change
        )

        self.ripper_executor = None

        super(Ripping, self).__init__(daemon_config, debug)

    def setup_postfork(self):
        self.state_sender = Sender(
            channel_state,
            name='ripping',
            io_loop=self.io_loop
        )

        self.command_receiver = self.setup_command_receiver(channel_command)

    def run(self):
        # for i in range(15):
        #     self.io_loop.add_timeout(time.time() + i, self.send_current_state)

        self.io_loop.start()

    def send_current_state(self):
        self.state_sender.send(json.dumps(self.state_machine.get_full_state()))

    def rip_disc(self, track_count):
        try:
            for i in range(track_count):
                self.state_machine.rip_track()
            self.state_machine.finish()
            logger.info('Disc successfully ripped')
        except:
            logger.exception('Oops, something went wrong')

    #
    # Interface with the world

    def grab_and_convert_track(self, track_number):
        (_, tmp_filename) = tempfile.mkstemp()

        cd_paranoia = subprocess.Popen(['cd-paranoia', '-S', '4', '-q', str(track_number), '-'], stdout=subprocess.PIPE)
        ffmpeg = subprocess.Popen(
            ['ffmpeg', '-loglevel', 'quiet', '-y', '-i', '-','-f', 'flac', tmp_filename],
            stdin=cd_paranoia.stdout,
            stdout=subprocess.PIPE
        )
        cd_paranoia.stdout.close()
        out, err = ffmpeg.communicate()

        return tmp_filename

    def create_folder(self, folder_path):
        if not folder_path.is_dir():
            logger.info('Creating folder in the media library %s', folder_path)
            folder_path.mkdir(parents=True)
        else:
            logger.info('Destination folder already existed')

    def move_track(self, source_path, target_path):
        logger.info('Moving track to final destination %s', target_path)
        shutil.copy(source_path, target_path)
        source_path.unlink()

    def write_disc_id(self, path, disc_id):
        path.write_text(disc_id)

    def clean_up_on_fail(self):
        pass
        # TODO: delete the album folder

    #
    # State machine events

    def on_state_change(self):
        self.send_current_state()

    #
    # Receive commands

    def command_start(self, args):
        self.ripper_executor = ThreadPoolExecutor(max_workers=1)
        disc_meta = json.loads(args[0])
        track_count = len(disc_meta['tracks'])
        self.state_machine.start(disc_meta)
        self.ripper_executor.submit(self.rip_disc, track_count)

    def command_known_disc(self, args):
        self.state_machine.known_disc()

    def command_eject(self, args):
        if self.ripper_executor:
            self.ripper_executor.shutdown(wait=False)
            self.ripper_executor = None
        self.state_machine.eject()

    def command_state(self, args):
        self.send_current_state()
