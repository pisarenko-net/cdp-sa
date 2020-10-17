from enum import Enum
import logging
from pathlib import Path

from transitions import Machine

from ..config import ALBUM_FOLDER_NAME_TEMPLATE
from ..config import MUSIC_PATH_NAME
from ..config import TRACK_FILE_NAME_TEMPLATE
from ..config import VA_ALBUM_FOLDER_NAME_TEMPLATE


logger = logging.getLogger(__name__)


class States(Enum):
    NO_DISC = 1
    KNOWN_DISC = 2
    RIPPING = 3
    DONE = 4


class Triggers(object):
    START = 'start'
    KNOWN_DISC = 'known_disc'
    RIP_TRACK = 'rip_track'
    FINISH = 'finish'
    EJECT = 'eject'


class Ripper(object):
    def __init__(
        self,
        grab_and_convert_track_func,
        create_folder_func,
        write_meta_func,
        move_track_func,
        write_disc_id_func,
        after_state_change_callback
    ):
        self.grab_and_convert_track_func = grab_and_convert_track_func
        self.create_folder_func = create_folder_func
        self.write_meta_func = write_meta_func
        self.move_track_func = move_track_func
        self.write_disc_id_func = write_disc_id_func

        self.after_state_change_callback = after_state_change_callback

        self._clear_internal_state()

    def _clear_internal_state(self):
        self.disc_meta = None
        self.track_list = None
        self.current_track = None
        self.folder_path = None

    def set_disc_meta(self, disc_meta):
        self.disc_meta = disc_meta
        self.track_list = []
        self.current_track = 0

    def create_folder(self, disc_meta):
        self.folder_path = self._get_folder_path(disc_meta)
        self.create_folder_func(self.folder_path)

    def _get_folder_path(self, disc_meta):
        album_path = Path(MUSIC_PATH_NAME)

        if 'artist' in disc_meta:
            album_path = album_path.joinpath(
                self._remove_unsafe_chars(
                    ALBUM_FOLDER_NAME_TEMPLATE.format(
                        artist=disc_meta['artist'],
                        title=disc_meta['title']
                    )
                )
            )
        else:
            album_path = album_path.joinpath(
                self._remove_unsafe_chars(
                    VA_ALBUM_FOLDER_NAME_TEMPLATE.format(title=disc_meta['title'])
                )
            )

        if disc_meta['total_cds'] > 1:
            album_path = album_path.joinpath('CD%s' % disc_meta['cd'])

        return album_path

    def _remove_unsafe_chars(self, path_name):
        return path_name.replace('\\', ' ')\
                        .replace('/', ' ')\
                        .replace(':', ' ')

    def has_next_track(self):
        return self.current_track < len(self.disc_meta['tracks'])

    def rip_next_track(self):
        track_number = self.current_track + 1
        logger.info('Ripping track %s', track_number)

        tmp_file_path = Path(self.grab_and_convert_track_func(track_number))

        self.tag_track(track_number, str(tmp_file_path))

        target_path = self.folder_path.joinpath(
            self._get_track_filename(track_number)
        )
        self.move_track_func(tmp_file_path, target_path)

        self.track_list.append(str(target_path))
        self.current_track = track_number
        self.after_state_change_callback()

    def tag_track(self, track_number, track_filename):
        track_meta = self.disc_meta['tracks'][track_number - 1]

        self.write_meta_func(
            track_filename,
            track_meta['artist'],
            track_meta['title'],
            self.disc_meta['title'],
            track_number,
            len(self.disc_meta['tracks'])
        )

    def _get_track_filename(self, track_number):
        track_meta = self.disc_meta['tracks'][track_number - 1]

        track_filename = TRACK_FILE_NAME_TEMPLATE.format(
            track_number="{:02d}".format(track_number),
            artist=track_meta['artist'],
            title=track_meta['title']
        )

        return self._remove_unsafe_chars(track_filename)

    def store_disc_id(self):
        disc_id = self.disc_meta['disc_id']
        path = self.folder_path.joinpath('.disc_id')
        self.write_disc_id_func(path, disc_id)

    def get_full_state(self):
        return {
            'state': self.state.value,
            'track_list': self.track_list,
            'disc_meta': self.disc_meta,
            'current_track': self.current_track,
            'folder_path': str(self.folder_path)
        }

    def on_state_change(self, *args, **kwargs):
        self.after_state_change_callback()


def create_ripper(
    grab_and_convert_track_func,
    create_folder_func,
    write_meta_func,
    move_track_func,
    write_disc_id_func,
    after_state_change_callback
):
    ripper = Ripper(
        grab_and_convert_track_func,
        create_folder_func,
        write_meta_func,
        move_track_func,
        write_disc_id_func,
        after_state_change_callback
    )

    machine = Machine(ripper, states=States, initial=States.NO_DISC, after_state_change='on_state_change')

    # terminal state: disc already ripped
    machine.add_transition(Triggers.KNOWN_DISC, States.NO_DISC, States.KNOWN_DISC)

    machine.add_transition(
        Triggers.START,
        States.NO_DISC,
        States.RIPPING,
        before=['set_disc_meta', 'create_folder']
    )

    machine.add_transition(
        Triggers.RIP_TRACK,
        States.RIPPING,
        States.RIPPING,
        conditions='has_next_track',
        before='rip_next_track'
    )

    # terminal state: disc ripped successfully
    machine.add_transition(
        Triggers.FINISH,
        States.RIPPING,
        States.DONE,
        unless='has_next_track',
        before='store_disc_id'
    )

    machine.add_transition(Triggers.EJECT, '*', States.NO_DISC, before='_clear_internal_state')

    return ripper
