import logging
import unittest
from unittest.mock import call, MagicMock

from hifi_appliance.constants import SAMPLE_RATE
from hifi_appliance.state import create_player
from hifi_appliance.state import PlayerStates


class PlaybackNewDiscTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

        self.track_list = ['/fake_path/01 track.flac', '/fake_path/02 track.flac']
        self.disc_meta = {'key': 'value'}

        self.start_audio_func = MagicMock()
        self.buffer_audio_func = MagicMock()
        self.stop_audio_func = MagicMock()
        self.pause_audio_func = MagicMock()
        self.resume_audio_func = MagicMock()
        self.after_state_change_callback = MagicMock()

        self.player = self._create_mocked_player()

    def _create_mocked_player(self):
        return create_player(
            self.start_audio_func,
            self.buffer_audio_func,
            self.stop_audio_func,
            self.pause_audio_func,
            self.resume_audio_func,
            self.after_state_change_callback
        )

    def test_machine_created(self):
        self.assertEqual(
            self.player.state, PlayerStates.INIT,
            'Player begins in INIT state'
        )

    def test_cd_becomes_ready(self):
        self.assertTrue(self.player.init())
        self.player.start(self.track_list, self.disc_meta)

        self.assertIs(self.player.track_list, self.track_list)
        self.assertIs(self.player.disc_meta, self.disc_meta)

        self.assertEqual(self.player.state, PlayerStates.STOPPED)

    def test_non_audio_cd_fails(self):
        self.assertTrue(self.player.init())

        self.assertTrue(self.player.unknown_disc())

        self.assertEqual(self.player.state, PlayerStates.UNKNOWN_DISC)


class TrackChangingTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

        self.track_list = [
            '/fake_path/01 track.flac',
            '/fake_path/02 track.flac',
            '/fake_path/03 track.flac',
            '/fake_path/04 track.flac',
        ]
        self.disc_meta = {
            'disc_id': 'disc_id',
            'tracks': [
                {},
                {},
                {},
                {}
            ]
        }

        self.start_audio_func = MagicMock()
        self.buffer_audio_func = MagicMock()
        self.stop_audio_func = MagicMock()
        self.pause_audio_func = MagicMock()
        self.resume_audio_func = MagicMock()
        self.after_state_change_callback = MagicMock()

        self.player = self._create_mocked_player()
        self._get_player_to_stopped()

    def _create_mocked_player(self):
        return create_player(
            self.start_audio_func,
            self.buffer_audio_func,
            self.stop_audio_func,
            self.pause_audio_func,
            self.resume_audio_func,
            self.after_state_change_callback
        )

    def _get_player_to_stopped(self):
        self.player.init()
        self.player.start(self.track_list, self.disc_meta)

    def test_next_when_stopped(self):
        self.assertEqual(self.player.current_track, 1)
        self.player.next()
        self.assertEqual(self.player.state, PlayerStates.STOPPED)
        self.assertEqual(self.player.current_track, 2)

    def test_prev_when_stopped(self):
        self.assertEqual(self.player.state, PlayerStates.STOPPED)
        self.player.next()
        self.player.next()
        self.player.next()
        self.assertEqual(self.player.current_track, 4)
        self.player.prev()
        self.assertEqual(self.player.state, PlayerStates.STOPPED)
        self.assertEqual(self.player.current_track, 3)
        self.player.prev()
        self.player.prev()
        self.assertEqual(self.player.state, PlayerStates.STOPPED)
        self.assertEqual(self.player.current_track, 1)

    def test_next_out_of_bounds(self):
        for x in range(1, 10):
            self.player.next()

        self.assertEqual(self.player.current_track, 4)

    def test_prev_out_of_bounds(self):
        for x in range(1, 10):
            self.player.next()

        for x in range(1, 100):
            self.player.prev()

        self.assertEqual(self.player.current_track, 1)

    def test_next_when_playing(self):
        self.assertEqual(self.player.current_track, 1)
        self.player.play()
        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.player.next()
        self.assertEqual(self.player.current_track, 2)
        self.assertEqual(self.player.state, PlayerStates.PLAYING)

    def test_prev_when_playing(self):
        self.player.play()
        self.player.next()
        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.assertEqual(self.player.current_track, 2)
        self.player.prev()
        self.assertEqual(self.player.current_track, 1)
        self.assertEqual(self.player.state, PlayerStates.PLAYING)

    def test_next_when_paused(self):
        self.assertEqual(self.player.current_track, 1)
        self.player.play()
        self.player.pause()
        self.assertEqual(self.player.state, PlayerStates.PAUSED)
        self.player.next()
        self.assertEqual(self.player.current_track, 2)
        self.assertEqual(self.player.state, PlayerStates.STOPPED)

    def test_prev_when_paused(self):
        self.player.play()
        self.player.next()
        self.player.pause()
        self.assertEqual(self.player.state, PlayerStates.PAUSED)
        self.assertEqual(self.player.current_track, 2)
        self.player.prev()
        self.assertEqual(self.player.current_track, 1)
        self.assertEqual(self.player.state, PlayerStates.STOPPED)

    def test_next_waiting_and_no_next_track(self):
        self.track_list = []
        self.player = self._create_mocked_player()
        self._get_player_to_stopped()

        self.player.play()
        self.assertEqual(self.player.state, PlayerStates.WAITING_FOR_DATA)
        self.player.next()
        self.assertEqual(self.player.state, PlayerStates.WAITING_FOR_DATA)
        self.assertEqual(self.player.current_track, 2)

    def test_prev_waiting_and_no_data(self):
        self.track_list = []
        self.check_disc_db_func = MagicMock(return_value=False)
        self.get_new_disc_func = MagicMock(return_value=(self.track_list, self.disc_meta))
        self.player = self._create_mocked_player()
        self._get_player_to_stopped()

        self.player.play()
        self.player.next()
        self.player.next()
        self.player.next()
        self.assertEqual(self.player.state, PlayerStates.WAITING_FOR_DATA)
        self.assertEqual(self.player.current_track, 4)
        self.player.prev()
        self.player.prev()
        self.assertEqual(self.player.state, PlayerStates.WAITING_FOR_DATA)
        self.assertEqual(self.player.current_track, 2)

    def test_prev_waiting_and_there_is_prev(self):
        self.track_list = ['/fake_path/01 track.flac']
        self.player = self._create_mocked_player()
        self._get_player_to_stopped()

        self.player.next()
        self.player.play()
        self.assertEqual(self.player.state, PlayerStates.WAITING_FOR_DATA)
        self.assertEqual(self.player.current_track, 2)
        self.player.prev()
        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.assertEqual(self.player.current_track, 1)

    def test_paused_player_stops(self):
        self.player.play()
        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.player.pause()
        self.assertEqual(self.player.state, PlayerStates.PAUSED)
        self.player.stop()
        self.assertEqual(self.player.state, PlayerStates.STOPPED)

    def test_waiting_player_stop(self):
        self.track_list = ['/fake_path/01 track.flac']
        self.player = self._create_mocked_player()
        self._get_player_to_stopped()

        self.player.next()
        self.player.play()
        self.assertEqual(self.player.state, PlayerStates.WAITING_FOR_DATA)
        self.player.stop()
        self.assertEqual(self.player.state, PlayerStates.STOPPED)

class AudioInteractionTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

        self.track_list = [
            '/fake_path/01 track.flac',
            '/fake_path/02 track.flac',
            '/fake_path/03 track.flac',
            '/fake_path/04 track.flac',
        ]
        self.disc_meta = {
            'disc_id': 'disc_id',
            'tracks': [
                {},
                {},
                {},
                {}
            ]
        }
        self.track_frames_total = 2 * 60 * SAMPLE_RATE  # 2 minutes

        self.start_audio_func = MagicMock()
        self.buffer_audio_func = MagicMock(return_value=self.track_frames_total)
        self.stop_audio_func = MagicMock()
        self.pause_audio_func = MagicMock()
        self.resume_audio_func = MagicMock()
        self.after_state_change_callback = MagicMock()

        self.player = self._create_mocked_player()
        self._get_player_to_stopped()

    def _create_mocked_player(self):
        return create_player(
            self.start_audio_func,
            self.buffer_audio_func,
            self.stop_audio_func,
            self.pause_audio_func,
            self.resume_audio_func,
            self.after_state_change_callback
        )

    def _get_player_to_stopped(self):
        self.player.init()
        self.player.start(self.track_list, self.disc_meta)

    def test_play_buffers_first_track(self):
        self.player.play()
        self.buffer_audio_func.assert_called_once_with('/fake_path/01 track.flac')

    def test_next_track_buffered_on_time(self):
        self.player.play()
        frames_20_sec = 20 * SAMPLE_RATE
        # notify state machine we're close to the end
        self.player.playing(self.track_frames_total - frames_20_sec)

        self.buffer_audio_func.assert_has_calls([
            call('/fake_path/01 track.flac'),
            call('/fake_path/02 track.flac')
        ])

    def test_next_track_not_buffered_too_early(self):
        self.player.play()
        frames_20_sec = 20 * SAMPLE_RATE
        # notify state machine we're just past 20 second mark
        self.player.playing(frames_20_sec)

        self.buffer_audio_func.assert_called_once_with('/fake_path/01 track.flac')

    def test_audio_stop_causes_finish(self):
        self.player.play()
        self.player.next()
        self.player.next()
        self.player.next()
        frames_20_sec = 20 * SAMPLE_RATE
        self.player.playing(frames_20_sec)

        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.player.finish()
        self.assertEqual(self.player.state, PlayerStates.STOPPED)
        self.assertEqual(self.player.current_track, 4)
        self.assertEqual(self.player.current_frame, None)
        self.assertEqual(self.player.total_frames, None)
        self.assertEqual(self.player.next_track_frames, None)

    def test_track_transition(self):
        self.buffer_audio_func = MagicMock(side_effect=[80000, 60000, 90000])
        self.player = self._create_mocked_player()
        self._get_player_to_stopped()

        # play first 380 frames
        self.player.play()
        self.player.playing(380)

        # expect next track to be buffered because the gap is too small
        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.assertEqual(self.player.current_track, 1)
        self.assertEqual(self.player.total_frames, 80000)
        self.assertEqual(self.player.current_frame, 380)
        self.assertEqual(self.player.next_track_frames, 60000)

        # play over the boundary of the current track
        self.player.playing(80000 + 30000)

        # expect current track number to increment
        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.assertEqual(self.player.current_track, 2)
        self.assertEqual(self.player.total_frames, 60000)
        self.assertEqual(self.player.current_frame, 30380)
        self.assertEqual(self.player.next_track_frames, None)

        # one additional frame triggers another track to be buffered
        self.player.playing(1)

        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.assertEqual(self.player.current_track, 2)
        self.assertEqual(self.player.total_frames, 60000)
        self.assertEqual(self.player.current_frame, 30381)
        self.assertEqual(self.player.next_track_frames, 90000)

    def test_audio_out_while_next_track_not_ready(self):
        # album with 4 tracks but only first is ready for playback
        self.track_list = ['/fake_path/01 track.flac']
        self.buffer_audio_func = MagicMock(return_value=980000)
        self.player = self._create_mocked_player()
        self._get_player_to_stopped()

        self.player.play()

        self.assertEqual(self.player.state, PlayerStates.PLAYING)
        self.assertEqual(self.player.current_track, 1)

        # simulate buffer almost empty, give a chance to fill but nothing to fill with
        self.player.playing(980000 - 200)

        self.buffer_audio_func.assert_called_once_with('/fake_path/01 track.flac')

        self.player.finish()
        self.assertEqual(self.player.state, PlayerStates.WAITING_FOR_DATA)
        self.assertEqual(self.player.current_track, 2)
