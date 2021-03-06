from enum import Enum
import logging
import threading

from transitions import Machine

from ..constants import NEXT_TRACK_BUFFER_THRESHOLD_SECONDS
from ..constants import SAMPLE_RATE


logger = logging.getLogger(__name__)


class States(Enum):
	INIT = 0
	NO_DISC = 1
	UNKNOWN_DISC = 2
	STOPPED = 3
	PLAYING = 4
	PAUSED = 5
	WAITING_FOR_DATA = 6


class Triggers(object):
	INIT = 'init'
	START = 'start'
	UNKNOWN_DISC = 'unknown_disc'
	PLAY = 'play'
	PLAYING = 'playing'  # called to notify of playback progress
	STOP = 'stop'
	PAUSE = 'pause'
	NEXT = 'next'
	PREV = 'prev'
	FINISH = 'finish'  # called when audio ran out of frames
	RIPPER_UPDATE = 'ripper_update'
	EJECT = 'eject'


class Player(object):
	def __init__(
		self,
		create_audio_func,
		buffer_track_func,
		stop_audio_func,
		pause_playback_func,
		resume_playback_func,
		after_state_change_callback
	):

		self.create_audio_func = create_audio_func
		self.buffer_track_func = buffer_track_func
		self.stop_audio_func = stop_audio_func
		self.pause_playback_func = pause_playback_func
		self.resume_playback_func = resume_playback_func

		self.after_state_change_callback = after_state_change_callback

		self.buffering_lock = threading.RLock()

		self._clear_internal_state()

	def _clear_internal_state(self):
		self.track_list = []
		self.disc_meta = {}

		self.current_track = 1
		self._clear_track_progress()

	def _clear_track_progress(self):
		self.current_frame = None
		self.total_frames = None
		self.next_track_frames = None

	def get_full_state(self):
		return {
			'state': self.state.value,
			'track_list': self.track_list,
			'disc_meta': self.disc_meta,
			'current_track': self.current_track,
			'current_frame': self.current_frame,
			'total_frames': self.total_frames,
			'next_track_frames': self.next_track_frames
		}

	#
	# Internal conditionals

	def is_no_disc_meta(self):
		return not self.disc_meta

	def is_flac_available(self, track_number=None):
		if not track_number:
			track_number = self.current_track
		return track_number <= len(self.track_list)

	def is_next_flac_available(self):
		return self.is_flac_available(self.current_track + 1)

	def is_prev_flac_available(self):
		return self.is_flac_available(self.current_track - 1)

	#
	# External interface (callbacks)

	def start_playback(self):
		'''Creates a new audio device and sets it up. Called once for a
		continuous playback stream.'''
		self.current_frame = 0
		self.create_audio_func()

		self.total_frames = self.buffer_track_func(
			self.track_list[self.current_track - 1]
		)

		self.resume_playback_func()

	def stop_playback(self):
		self.stop_audio_func()
		self._clear_track_progress()

	def pause_playback(self):
		self.pause_playback_func()

	def resume_playback(self):
		self.resume_playback_func()

	def on_state_change(self, *args, **kwargs):
		self.after_state_change_callback()

	#
	# Internal state changes

	def set_disc_meta(self, track_list, disc_meta):
		self.track_list = track_list
		self.disc_meta = disc_meta

	def next_track(self):
		self.current_track += 1

	def prev_track(self):
		self.current_track -= 1

	def has_prev_track(self):
		return self.current_track > 1

	def has_next_track(self):
		return self.current_track < len(self.disc_meta['tracks'])

	def update_position(self, frames):
		self.current_frame += frames

		try:
			if self.buffering_lock.acquire(blocking=False):
				next_track_index = self.current_track
				next_track_number = self.current_track + 1

				if self._should_buffer_next_track() and self.is_flac_available(next_track_number):
					self.next_track_frames = self.buffer_track_func(
						self.track_list[next_track_index]
					)

				if self._track_changed():
					self.current_frame -= self.total_frames
					self.total_frames = self.next_track_frames
					self.next_track_frames = None
					self.current_track += 1
		finally:
			self.buffering_lock.release()

	def _should_buffer_next_track(self):
		already_buffered = self.next_track_frames is not None
		remaining_frames = self.total_frames - self.current_frame
		less_than_x_seconds_remaining = (remaining_frames // SAMPLE_RATE) < NEXT_TRACK_BUFFER_THRESHOLD_SECONDS
		return less_than_x_seconds_remaining and not already_buffered

	def _track_changed(self):
		'''Assume track changed when more than 0.5 seconds extra frames
		were played. Sample rate 44.1k gives us frames per second.'''
		return (self.current_frame - self.total_frames) > (SAMPLE_RATE // 2)

	def update_track_list(self, track_list=None):
		if track_list:
			self.track_list = track_list


def create_player(
	create_audio_func,
	buffer_track_func,
	stop_audio_func,
	pause_playback_func,
	resume_playback_func,
	after_state_change_callback,
):

	player = Player(
		create_audio_func,
		buffer_track_func,
		stop_audio_func,
		pause_playback_func,
		resume_playback_func,
		after_state_change_callback
	)
	machine = Machine(player, states=States, initial=States.INIT, after_state_change='on_state_change')

	#
	# External triggers
	machine.add_transition(
		Triggers.UNKNOWN_DISC,
		States.NO_DISC,
		States.UNKNOWN_DISC
	)
	machine.add_transition(
		Triggers.START,
		States.NO_DISC,
		States.STOPPED,
		before='set_disc_meta'
	)

	#
	# Disc playback
	machine.add_transition(
		Triggers.PLAY,
		States.STOPPED,
		States.WAITING_FOR_DATA,
		unless='is_flac_available',
	)
	machine.add_transition(
		Triggers.PLAY,
		[States.WAITING_FOR_DATA, States.STOPPED],
		States.PLAYING,
		conditions='is_flac_available',
		before='start_playback'
	)
	machine.add_transition(Triggers.PLAY, States.PAUSED, States.PLAYING, before='resume_playback')
	machine.add_transition(Triggers.PLAYING, States.PLAYING, States.PLAYING, before='update_position')
	machine.add_transition(
		Triggers.STOP,
		[States.PLAYING, States.PAUSED, States.WAITING_FOR_DATA],
		States.STOPPED,
		before='stop_playback'
	)
	machine.add_transition(Triggers.PAUSE, States.PLAYING, States.PAUSED, before='pause_playback')

	machine.add_transition(
		Triggers.FINISH,
		States.PLAYING,
		States.STOPPED,
		unless=['has_next_track'],
		before='_clear_track_progress'
	)
	machine.add_transition(
		Triggers.FINISH,
		States.PLAYING,
		States.WAITING_FOR_DATA,
		conditions=['has_next_track'],
		unless=['is_next_flac_available'],
		before=['_clear_track_progress', 'next_track']
	)

	#
	# Track switching
	machine.add_transition(
		Triggers.NEXT,
		States.PLAYING,
		States.PLAYING,
		conditions=['has_next_track', 'is_next_flac_available'],
		before=['stop_playback', 'next_track', 'start_playback']
	)
	machine.add_transition(
		Triggers.PREV,
		States.PLAYING,
		States.PLAYING,
		conditions=['has_prev_track'],
		before=['stop_playback', 'prev_track', 'start_playback']
	)

	machine.add_transition(
		Triggers.NEXT,
		States.STOPPED,
		States.STOPPED,
		conditions=['has_next_track'],
		before=['next_track']
	)
	machine.add_transition(
		Triggers.PREV,
		States.STOPPED,
		States.STOPPED,
		conditions=['has_prev_track'],
		before=['prev_track']
	)

	machine.add_transition(
		Triggers.NEXT,
		States.PAUSED,
		States.STOPPED,
		conditions=['has_next_track'],
		before=['next_track', 'stop_playback']
	)
	machine.add_transition(
		Triggers.PREV,
		States.PAUSED,
		States.STOPPED,
		conditions=['has_prev_track'],
		before=['prev_track', 'stop_playback']
	)

	machine.add_transition(
		Triggers.NEXT,
		States.WAITING_FOR_DATA,
		States.PLAYING,
		conditions=['has_next_track', 'is_next_flac_available'],
		before=['next_track', 'start_playback']
	)
	machine.add_transition(
		Triggers.PREV,
		States.WAITING_FOR_DATA,
		States.PLAYING,
		conditions=['has_prev_track', 'is_prev_flac_available'],
		before=['prev_track', 'start_playback']
	)
	machine.add_transition(
		Triggers.NEXT,
		States.PLAYING,
		States.WAITING_FOR_DATA,
		conditions=['has_next_track'],
		unless=['is_next_flac_available'],
		before=['next_track']
	)
	machine.add_transition(
		Triggers.NEXT,
		States.WAITING_FOR_DATA,
		States.WAITING_FOR_DATA,
		conditions=['has_next_track'],
		unless=['is_next_flac_available'],
		before=['next_track']
	)
	machine.add_transition(
		Triggers.PREV,
		States.WAITING_FOR_DATA,
		States.WAITING_FOR_DATA,
		conditions=['has_prev_track'],
		unless=['is_prev_flac_available'],
		before=['prev_track']
	)

	#
	# Ripper interaction
	machine.add_transition(
		Triggers.RIPPER_UPDATE,
		[States.PLAYING, States.STOPPED, States.PAUSED, States.WAITING_FOR_DATA],
		'=',
		before='update_track_list'
	)

	#
	# Eject
	machine.add_transition(Triggers.EJECT, '*', States.NO_DISC, before=['stop_playback', '_clear_internal_state'])

	machine.add_transition(Triggers.INIT, States.INIT, States.NO_DISC)

	return player
