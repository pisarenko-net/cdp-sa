from enum import Enum


class Command(Enum):
	DISC = 'disc'
	EJECT = 'eject'
	PLAY = 'play'
	STOP = 'stop'
	PAUSE = 'pause'
	NEXT = 'next'
	PREV = 'prev'
	CLEAR = 'clear'
	OK = 'ok'
