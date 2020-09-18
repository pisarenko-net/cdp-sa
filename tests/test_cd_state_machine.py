import unittest
from unittest.mock import MagicMock

from hifi_appliance.state import create_player
from hifi_appliance.state import PlayerStates


_DISC_ENTRY = {'key': 'value'}
_DISC_META = {'key': 'value'}


class PlaybackNewDiscTestCase(unittest.TestCase):
	def setUp(self):
		self.read_disc_func = MagicMock(return_value='disc_id')
		self.check_disc_db_func = MagicMock(return_value=True)
		self.get_disc_meta_db_func = MagicMock(return_value=(_DISC_ENTRY, _DISC_META))
		self.get_disc_meta_online_func = MagicMock(return_value=(_DISC_ENTRY, _DISC_META))
		self.eject_func = MagicMock()

		self.begin_playback_callback = MagicMock()
		self.stop_playback_callback = MagicMock()
		self.pause_playback_callback = MagicMock()

		self.player = self._create_mocked_player()

	def _create_mocked_player(self):
		return create_player(
			self.read_disc_func,
			self.check_disc_db_func,
			self.get_disc_meta_db_func,
			self.get_disc_meta_online_func,
			self.eject_func,
			self.begin_playback_callback,
			self.stop_playback_callback,
			self.pause_playback_callback
		)

	def test_machine_created(self):
		self.assertEqual(
			self.player.state, PlayerStates.INIT,
			'Player begins in INIT state'
		)

	def test_new_cd_online_query_fails(self):
		"""
		A previously unplayed CD has been inserted. Online metadata lookup
		fails. It is expected for the player to end in a terminal UNKOWN DISC
		state.
		"""
		self.check_disc_db_func = MagicMock(return_value=False)
		self.get_disc_meta_online_func = MagicMock(return_value=(None, None))
		self.player = self._create_mocked_player()

		self.assertTrue(self.player.init())

		self.assertEqual(self.player.disc_id, None)
		self.assertTrue(self.player.read_disc())
		self.assertEqual(self.player.disc_id, 'disc_id')

		self.assertEqual(self.player.in_db, None)

		self.assertTrue(self.player.check_disc())

		self.assertEqual(self.player.in_db, False)

		self.assertEqual(self.player.disc_entry, None)
		self.assertEqual(self.player.disc_meta, None)

		self.assertTrue(self.player.query_disc())

		self.get_disc_meta_db_func.assert_not_called()
		self.get_disc_meta_online_func.assert_called()
		self.assertEqual(self.player.disc_entry, None)
		self.assertEqual(self.player.disc_meta, None)
		self.assertEqual(self.player.state, PlayerStates.UNKNOWN_DISC)

	def test_known_cd_becomes_ready(self):
		"""
		A previously played CD has been inserted. Local DB look-up succeeds. It
		is expected player to get be for playback (state STOPPED).
		"""
		self.assertTrue(self.player.init())

		self.assertTrue(self.player.read_disc())

		self.assertTrue(self.player.check_disc())

		self.assertEqual(self.player.in_db, True)

		self.assertTrue(self.player.query_disc())

		self.get_disc_meta_db_func.assert_called()
		self.get_disc_meta_online_func.assert_not_called()
		self.assertIs(self.player.disc_entry, _DISC_ENTRY)
		self.assertIs(self.player.disc_meta, _DISC_META)

		self.assertEqual(self.player.state, PlayerStates.STOPPED)

	def test_new_cd_becomes_ready(self):
		"""
		A previously unplayed CD has been inserted. Online metadata lookup
		succeeds. It is expected for the player to be ready for playback (state
		stopped).
		"""
		self.check_disc_db_func = MagicMock(return_value=False)
		self.player = self._create_mocked_player()

		self.assertTrue(self.player.init())

		self.assertTrue(self.player.read_disc())

		self.assertTrue(self.player.check_disc())

		self.assertEqual(self.player.in_db, False)

		self.assertTrue(self.player.query_disc())

		self.get_disc_meta_db_func.assert_not_called()
		self.get_disc_meta_online_func.assert_called()
		self.assertIs(self.player.disc_entry, _DISC_ENTRY)
		self.assertIs(self.player.disc_meta, _DISC_META)

		self.assertEqual(self.player.state, PlayerStates.STOPPED)
