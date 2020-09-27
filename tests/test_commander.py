# this code has been moved out of playback state machine and needs to make its
# way back

	# machine.add_transition(
	# 	Triggers.READ_DISC,
	# 	States.NO_DISC,
	# 	States.DISC_ID,
	# 	conditions='has_disc_id',
	# 	prepare='read_disc_id'
	# )
	# machine.add_transition(
	# 	Triggers.READ_DISC,
	# 	States.NO_DISC,
	# 	States.UNKNOWN_DISC,
	# 	unless='has_disc_id'
	# )
	# machine.add_transition(Triggers.CHECK_DISC, States.DISC_ID, States.LOOK_UP, before='check_disc_in_db')
	# machine.add_transition(
	# 	Triggers.QUERY_DISC,
	# 	States.LOOK_UP,
	# 	States.STOPPED,
	# 	conditions='is_disc_in_db',
	# 	before='get_disc_meta_db'
	# )
	# machine.add_transition(
	# 	Triggers.QUERY_DISC,
	# 	States.LOOK_UP,
	# 	States.STOPPED,
	# 	unless='is_no_disc_meta',
	# 	prepare='get_disc_meta_online'
	# )
	# machine.add_transition(Triggers.QUERY_DISC, States.LOOK_UP, States.UNKNOWN_DISC, conditions='is_no_disc_meta')

 # class PlaybackNewDiscTestCase(unittest.TestCase):
 #    def setUp(self):
 #        logging.disable(logging.CRITICAL)

 #        self.track_list = ['/fake_path/01 track.flac', '/fake_path/02 track.flac']
 #        self.disc_meta = {'key': 'value'}

 #        self.read_disc_func = MagicMock(return_value='disc_id')
 #        self.check_disc_db_func = MagicMock(return_value=True)
 #        self.get_known_disc_func = MagicMock(return_value=(self.track_list, self.disc_meta))
 #        self.get_new_disc_func = MagicMock(return_value=(self.track_list, self.disc_meta))

 #        self.start_audio_func = MagicMock()
 #        self.buffer_audio_func = MagicMock()
 #        self.stop_audio_func = MagicMock()
 #        self.pause_audio_func = MagicMock()
 #        self.resume_audio_func = MagicMock()
 #        self.after_state_change_callback = MagicMock()

 #        self.player = self._create_mocked_player()

 #    def _create_mocked_player(self):
 #        return create_player(
 #            self.read_disc_func,
 #            self.check_disc_db_func,
 #            self.get_known_disc_func,
 #            self.get_new_disc_func,
 #            self.start_audio_func,
 #            self.buffer_audio_func,
 #            self.stop_audio_func,
 #            self.pause_audio_func,
 #            self.resume_audio_func,
 #            self.after_state_change_callback
 #        )

 #    def test_machine_created(self):
 #        self.assertEqual(
 #            self.player.state, PlayerStates.INIT,
 #            'Player begins in INIT state'
 #        )

 #    def test_new_cd_online_query_fails(self):
 #        """
 #        A previously unplayed CD has been inserted. Online metadata lookup
 #        fails. It is expected for the player to end in a terminal UNKOWN DISC
 #        state.
 #        """
 #        self.check_disc_db_func = MagicMock(return_value=False)
 #        self.get_new_disc_func = MagicMock(return_value=(None, None))
 #        self.player = self._create_mocked_player()

 #        self.assertTrue(self.player.init())

 #        self.assertEqual(self.player.disc_id, None)
 #        self.assertTrue(self.player.read_disc())
 #        self.assertEqual(self.player.disc_id, 'disc_id')

 #        self.assertEqual(self.player.in_db, None)

 #        self.assertTrue(self.player.check_disc())

 #        self.assertEqual(self.player.in_db, False)

 #        self.assertEqual(self.player.track_list, [])
 #        self.assertEqual(self.player.disc_meta, {})

 #        self.assertTrue(self.player.query_disc())

 #        self.get_known_disc_func.assert_not_called()
 #        self.get_new_disc_func.assert_called()
 #        self.assertEqual(self.player.track_list, None)
 #        self.assertEqual(self.player.disc_meta, None)
 #        self.assertEqual(self.player.state, PlayerStates.UNKNOWN_DISC)

 #    def test_known_cd_becomes_ready(self):
 #        """
 #        A previously played CD has been inserted. Local DB look-up succeeds. It
 #        is expected player to get be for playback (state STOPPED).
 #        """
 #        self.assertTrue(self.player.init())

 #        self.assertTrue(self.player.read_disc())

 #        self.assertTrue(self.player.check_disc())

 #        self.assertEqual(self.player.in_db, True)

 #        self.assertTrue(self.player.query_disc())

 #        self.get_known_disc_func.assert_called()
 #        self.get_new_disc_func.assert_not_called()
 #        self.assertIs(self.player.track_list, self.track_list)
 #        self.assertIs(self.player.disc_meta, self.disc_meta)

 #        self.assertEqual(self.player.state, PlayerStates.STOPPED)

 #    def test_new_cd_becomes_ready(self):
 #        """
 #        A previously unplayed CD has been inserted. Online metadata lookup
 #        succeeds. It is expected for the player to be ready for playback (state
 #        stopped).
 #        """
 #        self.check_disc_db_func = MagicMock(return_value=False)
 #        self.player = self._create_mocked_player()

 #        self.assertTrue(self.player.init())

 #        self.assertTrue(self.player.read_disc())

 #        self.assertTrue(self.player.check_disc())

 #        self.assertEqual(self.player.in_db, False)

 #        self.assertTrue(self.player.query_disc())

 #        self.get_known_disc_func.assert_not_called()
 #        self.get_new_disc_func.assert_called()
 #        self.assertIs(self.player.track_list, self.track_list)
 #        self.assertIs(self.player.disc_meta, self.disc_meta)

 #        self.assertEqual(self.player.state, PlayerStates.STOPPED)

 #    def test_non_audio_cd_fails(self):
 #        self.read_disc_func = MagicMock(return_value=None)
 #        self.player = self._create_mocked_player()

 #        self.assertTrue(self.player.init())

 #        self.assertTrue(self.player.read_disc())

 #        self.assertEqual(self.player.state, PlayerStates.UNKNOWN_DISC)