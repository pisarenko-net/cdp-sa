from enum import Enum
import time
from transitions import Machine

class States(Enum):
	INIT = 0
	NO_DISC = 1
	DISC_ID = 2
	READY = 4
	UNKNOWN_DISC = 5
	PLAYING = 6


class Player(object):
	def __init__(self):
		self.disc_id = None
		self.in_db = False
		self.disc_info = None
		self.track_info = None
		self.frame = 0

	def read_disc_id(self):
		print('reading disc id')

	def is_no_disc_info(self):
		return self.disc_info == None

	def query_disc(self):
		self.disc_info = True

	def update_progress(self, frame=0):
		self.frame = frame


player = Player()
machine = Machine(player, states=States, initial=States.INIT)

machine.add_transition('init', States.INIT, States.NO_DISC)
machine.add_transition('disc', States.NO_DISC, States.DISC_ID, before='read_disc_id')
machine.add_transition('query', States.DISC_ID, States.READY, unless='is_no_disc_info', prepare='query_disc')
machine.add_transition('query', States.DISC_ID, States.UNKNOWN_DISC, conditions='is_no_disc_info')
machine.add_transition('play', States.READY, States.PLAYING)
machine.add_transition('playing', States.PLAYING, States.PLAYING, before='update_progress')

player.init()
player.disc()
player.query()