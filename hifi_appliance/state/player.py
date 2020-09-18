from enum import Enum

from transitions import Machine


class States(Enum):
	INIT = 0
	NO_DISC = 1
	DISC_ID = 2
	LOOK_UP = 3
	UNKNOWN_DISC = 4
	STOPPED = 5
	PLAYING = 6
	PAUSED = 7
	WAITING_FOR_DATA = 8


class Triggers(object):
	INIT = 'init'
	READ_DISC = 'read_disc'
	CHECK_DISC = 'check_disc'
	QUERY_DISC = 'query_disc'
	PLAY = 'play'
	PLAYING = 'playing'
	STOP = 'stop'
	PAUSE = 'pause'
	NEXT = 'next'
	PREV = 'prev'
	RIPPER_TICK = 'ripper_tick'
	EJECT = 'eject'


class Player(object):
	"""
	Encapsulate state entire
	"""
	def __init__(
		self,
		read_disc_id_func,
		check_disc_db_func,
		get_disc_meta_db_func,
		get_disc_meta_online_func,
		eject_func,
		begin_playback_callback,
		stop_playback_callback,
		pause_playback_callback,
	):

		self.read_disc_id_func = read_disc_id_func
		self.check_disc_db_func = check_disc_db_func
		self.get_disc_meta_db_func = get_disc_meta_db_func
		self.get_disc_meta_online_func = get_disc_meta_online_func
		self.eject_func = eject_func

		self.begin_playback_callback = begin_playback_callback
		self.stop_playback_callback = stop_playback_callback
		self.pause_playback_callback = pause_playback_callback

		self.clear_internal_state()

	def clear_internal_state(self):
		self.disc_id = None
		self.in_db = None
		self.disc_entry = None
		self.disc_meta = None

		self.is_flac_available = None
		self.queued_track = None
		self.current_track = None
		self.current_frame = None

	def read_disc_id(self):
		self.disc_id = self.read_disc_id_func()

	def check_disc_in_db(self):
		self.in_db = self.check_disc_db_func()

	def is_disc_in_db(self):
		return self.in_db

	def get_disc_meta_db(self):
		(self.disc_entry, self.disc_meta) = self.get_disc_meta_db_func(self.disc_id)

	def get_disc_meta_online(self):
		(self.disc_entry, self.disc_meta) = self.get_disc_meta_online_func(self.disc_id)

	def is_no_disc_meta(self):
		return not self.disc_meta

	def set_track_number(self, track_number=1):
		self.queued_track = track_number

	def increment_track_number(self):
		self.queued_track += 1

	def decrement_track_number(self):
		self.queued_track -= 1

	def find_flac(self):
		# check if disc entry contains the queued track number
		self.is_flac_available = False

	def is_flac_available(self):
		return self.is_flac_available

	def begin_playback(self):
		self.current_track = self.queued_track
		# full file path name is available here
		self.begin_playback_callback()

	def stop_playback(self):
		self.stop_playback_callback()

		self.is_flac_available = None
		self.current_track = None
		self.current_frame = None
		self.queued_track = None

	def pause_playback(self):
		pass

	def resume_playback(self):
		pass

	def next_track(self):
		pass

	def prev_track(self):
		pass

	def has_prev_track(self):
		return self.queued_track > 1

	def has_next_track(self):
		return self.queued_track < self.disc_meta.count()

	def update_position(self, frame=None):
		self.current_frame = frame

	def update_disc_entry(self, disc_entry=None):
		if disc_entry:
			self.disc_entry = disc_entry


def create_player(
	read_disc_id_func,
	check_disc_db_func,
	get_disc_meta_db_func,
	get_disc_meta_online_func,
	eject_func,
	begin_playback_callback,
	stop_playback_callback,
	pause_playback_callback,
):

	player = Player(
		read_disc_id_func,
		check_disc_db_func,
		get_disc_meta_db_func,
		get_disc_meta_online_func,
		begin_playback_callback,
		stop_playback_callback,
		pause_playback_callback,
		eject_func
	)
	machine = Machine(player, states=States, initial=States.INIT)

	#
	# Disc identification
	machine.add_transition(Triggers.READ_DISC, States.NO_DISC, States.DISC_ID, before='read_disc_id')
	machine.add_transition(Triggers.CHECK_DISC, States.DISC_ID, States.LOOK_UP, before='check_disc_in_db')
	machine.add_transition(
		Triggers.QUERY_DISC,
		States.LOOK_UP,
		States.STOPPED,
		conditions='is_disc_in_db',
		before='get_disc_meta_db'
	)
	machine.add_transition(
		Triggers.QUERY_DISC,
		States.LOOK_UP,
		States.STOPPED,
		unless='is_no_disc_meta',
		prepare='get_disc_meta_online'
	)
	machine.add_transition(Triggers.QUERY_DISC, States.LOOK_UP, States.UNKNOWN_DISC, conditions='is_no_disc_meta')

	#
	# Disc playback
	machine.add_transition(
		Triggers.PLAY,
		States.STOPPED,
		States.WAITING_FOR_DATA,
		unless='is_flac_available',
		prepare=['set_track_number', 'find_flac']
	)
	machine.add_transition(
		Triggers.PLAY,
		States.STOPPED,
		States.PLAYING,
		conditions='is_flac_available',
		prepare='set_track_number',
		before='begin_playback'
	)
	machine.add_transition(Triggers.PLAY, States.PAUSED, States.PLAYING, before='resume_playback')
	machine.add_transition(Triggers.PLAYING, States.PLAYING, States.PLAYING, before='update_position')
	machine.add_transition(Triggers.STOP, States.PLAYING, States.STOPPED, before='stop_playback')
	machine.add_transition(Triggers.PAUSE, States.PLAYING, States.PAUSED, before='pause_playback')

	#
	# Track switching
	machine.add_transition(
		Triggers.PREV,
		[States.PLAYING, States.WAITING_FOR_DATA],
		States.PLAYING,
		conditions=['has_prev_track', 'is_flac_available'],
		prepare='decrement_track_number',
		before='prev_track'
	)
	machine.add_transition(
		Triggers.NEXT,
		[States.PLAYING, States.WAITING_FOR_DATA],
		States.PLAYING,
		conditions=['has_next_track', 'is_flac_available'],
		prepare='increment_track_number',
		before='next_track'
	)
	machine.add_transition(
		Triggers.NEXT,
		States.PLAYING,
		States.WAITING_FOR_DATA,
		conditions='has_next_track',
		unless='is_flac_available',
		before='stop_playback'
	)
	machine.add_transition(
		Triggers.PREV,
		States.PLAYING,
		States.WAITING_FOR_DATA,
		conditions='has_prev_track',
		unless='is_flac_available',
		before='stop_playback'
	)

	#
	# Ripper interaction
	machine.add_transition(
		Triggers.RIPPER_TICK,
		States.WAITING_FOR_DATA,
		States.PLAYING,
		conditions='is_flac_available',
		prepare='update_disc_entry',
		before='begin_playback'
	)

	#
	# Eject
	machine.add_transition(Triggers.EJECT, '*', States.NO_DISC, before=['stop_playback', 'clear_internal_state'])

	machine.add_transition(Triggers.INIT, States.INIT, States.NO_DISC)

	return player
