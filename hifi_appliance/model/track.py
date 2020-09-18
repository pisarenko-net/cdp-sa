class Track(object):
	pass


class PlaybackStatus(object):
	def __init__(self, duration):
		self.duration = duration
		self.position = 0
