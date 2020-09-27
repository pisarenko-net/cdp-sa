import threading
from queue import Queue

import zmq

from hifi_appliance.message_bus import state as channel_state
from hifi_appliance.message_bus import error as channel_error
from hifi_appliance.message_bus import command as channel_command
from hifi_appliance.message_bus import command_playback as channel_command_playback
from hifi_appliance.message_bus import command_ripper as channel_command_ripper
from hifi_appliance.message_bus import command_minidisc as channel_command_minidisc


CHANNELS = {
	'state': None,
	'error': None,
	'command': None,
	'command_playback': None,
	'command_ripper': None,
	'command_minidisc': None
}

COMMAND_QUEUE = Queue()


def run_send_loop():
	context = zmq.Context()

	channels = {
		'state': context.socket(zmq.PUB),
		'error': context.socket(zmq.PUB),
		'command': context.socket(zmq.PUSH),
		'command_playback': context.socket(zmq.PUSH),
		'command_ripper': context.socket(zmq.PUSH),
		'command_minidisc': context.socket(zmq.PUSH)
	}

	channels['state'].bind(channel_state._pub_addresses[b'ctl'])
	channels['error'].bind(channel_error._pub_addresses[b'ctl'])
	channels['command'].connect(channel_command._address)
	channels['command_playback'].connect(channel_command_playback._address)
	channels['command_ripper'].connect(channel_command_playback._address)
	channels['command_minidisc'].connect(channel_command_minidisc._address)

	while True:
		(channel, message) = COMMAND_QUEUE.get()
		socket = channels[channel]
		socket.send_multipart([message_part.encode('ascii') for message_part in message])


def main():
	send_thread = threading.Thread(
	    target=run_send_loop,
	    name='ctl'
	)
	send_thread.daemon = True
	send_thread.start()

	current_channel = 'command'
	print('Known channels: %s' % list(CHANNELS.keys()))

	while True:
		print('[%s] >' % (current_channel), end=' ')
		entered = input().split(' ')

		if entered[0] == 'set':
			CHANNELS[entered[1]]
			current_channel = entered[1]
			continue

		COMMAND_QUEUE.put((current_channel, entered))


if __name__ == '__main__':
	main()
