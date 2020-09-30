import logging
from pathlib import Path
import unittest
from unittest.mock import call, MagicMock

from hifi_appliance.config import MUSIC_PATH_NAME
from hifi_appliance.state import create_ripper
from hifi_appliance.state import RipperStates


class RipperNewDiscTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

        self.grab_and_convert_track_func = MagicMock(return_value='/tmp/blabla')
        self.create_folder_func = MagicMock()
        self.write_meta_func = MagicMock()
        self.move_track_func = MagicMock()
        self.write_disc_id_func = MagicMock()
        self.on_state_change_callback = MagicMock()

        self.ripper = create_ripper(
            self.grab_and_convert_track_func,
            self.create_folder_func,
            self.write_meta_func,
            self.move_track_func,
            self.write_disc_id_func,
            self.on_state_change_callback
        )

        self.disc_meta = {
            'disc_id': 'test_disc_id',
            'title': 'The Long One Gone',
            'artist': 'Positrons',
            'total_cds': 2,
            'cd': 1,
            'tracks': [{
                    'title': 'Good Days Outside',
                    'artist': 'Positrons'
                }, {
                    'title': 'Funny Grass',
                    'artist': 'Positrons'
                }, {
                    'title': 'Maybe Tomorrow',
                    'artist': 'Positrons'
            }]
        }

    def test_machine_created(self):
        self.assertEqual(
            self.ripper.state, RipperStates.IDLE,
            'Ripper begins in IDLE state'
        )

    def test_start_multi_cd(self):
        self.assertEqual(self.ripper.state, RipperStates.IDLE)
        self.ripper.start(self.disc_meta)

        self.assertEqual(self.ripper.state, RipperStates.RIPPING)

        self.create_folder_func.assert_called_once_with(
            Path(MUSIC_PATH_NAME).joinpath('Positrons - The Long One Gone', 'CD1')
        )

    def test_start_single_cd(self):
        self.disc_meta['total_cds'] = 1
        self.ripper.start(self.disc_meta)

        self.create_folder_func.assert_called_once_with(
            Path(MUSIC_PATH_NAME).joinpath('Positrons - The Long One Gone')
        )

    def test_start_va_disc(self):
        del self.disc_meta['artist']
        self.ripper.start(self.disc_meta)

        self.create_folder_func.assert_called_once_with(
            Path(MUSIC_PATH_NAME).joinpath('The Long One Gone', 'CD1')
        )

    def test_rip_tracks_progresses(self):
        self.ripper.start(self.disc_meta)

        self.assertTrue(self.ripper.rip_track())
        self.grab_and_convert_track_func.assert_called_with(1)

        self.assertTrue(self.ripper.rip_track())
        self.grab_and_convert_track_func.assert_called_with(2)

        self.assertTrue(self.ripper.rip_track())
        self.grab_and_convert_track_func.assert_called_with(3)

    def test_rip_beyond_tracks_fails(self):
        self.ripper.start(self.disc_meta)

        self.assertTrue(self.ripper.rip_track())
        self.assertTrue(self.ripper.rip_track())
        self.assertTrue(self.ripper.rip_track())

        self.assertFalse(self.ripper.rip_track())
        self.grab_and_convert_track_func.assert_called_with(3)

    def test_track_final_path(self):
        expected_track_path = Path(MUSIC_PATH_NAME).joinpath(
            'Positrons - The Long One Gone',
            'CD1',
            '01 Positrons - Good Days Outside.flac'
        )

        self.ripper.start(self.disc_meta)

        self.assertTrue(self.ripper.rip_track())
        self.move_track_func.assert_called_once_with(
            Path('/tmp/blabla'),
            expected_track_path
        )

    def test_finish_fails_when_not_done(self):
        self.ripper.start(self.disc_meta)
        self.assertFalse(self.ripper.finish())

    def test_finish(self):
        expected_disc_id_path = Path(MUSIC_PATH_NAME).joinpath(
            'Positrons - The Long One Gone',
            'CD1',
            '.disc_id'
        )

        self.ripper.start(self.disc_meta)
        self.assertTrue(self.ripper.rip_track())
        self.assertTrue(self.ripper.rip_track())
        self.assertTrue(self.ripper.rip_track())
        self.assertTrue(self.ripper.finish())

        self.assertEqual(self.ripper.state, RipperStates.DONE)
        self.write_disc_id_func.assert_called_once_with(
            expected_disc_id_path,
            'test_disc_id'
        )

    def test_complete_track_list_updated(self):
        expected_track_path = Path(MUSIC_PATH_NAME).joinpath(
            'Positrons - The Long One Gone',
            'CD1',
        )

        self.ripper.start(self.disc_meta)

        self.assertEqual(len(self.ripper.track_list), 0)
        self.assertTrue(self.ripper.rip_track())
        self.assertEqual(
            self.ripper.track_list[0],
            str(expected_track_path.joinpath('01 Positrons - Good Days Outside.flac'))
        )

        self.assertEqual(len(self.ripper.track_list), 1)
        self.assertTrue(self.ripper.rip_track())
        self.assertEqual(
            self.ripper.track_list[1],
            str(expected_track_path.joinpath('02 Positrons - Funny Grass.flac'))
        )

        self.assertEqual(len(self.ripper.track_list), 2)
        self.assertTrue(self.ripper.rip_track())
        self.assertEqual(
            self.ripper.track_list[2],
            str(expected_track_path.joinpath('03 Positrons - Maybe Tomorrow.flac'))
        )
