import threading
from queue import Queue
import sys

import lirc
import zmq

from hifi_appliance.message_bus import state as channel_state
from hifi_appliance.message_bus import error as channel_error
from hifi_appliance.message_bus import command as channel_command
from hifi_appliance.message_bus import command_playback as channel_command_playback
from hifi_appliance.message_bus import command_ripping as channel_command_ripping
from hifi_appliance.message_bus import command_minidisc as channel_command_minidisc


CHANNELS = {
    'state': None,
    'error': None,
    'command': None,
    'command_playback': None,
    'command_ripping': None,
    'command_minidisc': None,
    'lirc': None
}

COMMAND_QUEUE = Queue()

REMOTE_CONTROL = 'denon'

REMOTE_KEYS = {
    'play': 'KEY_PLAY',
    'pause': 'KEY_PAUSE',
    'stop': 'KEY_STOP',
    'next': 'KEY_NEXT',
    'prev': 'KEY_PREVIOUS',
    'eject': 'KEY_EJECTCD',
}


def run_send_loop():
    context = zmq.Context()

    channels = {
        'state': context.socket(zmq.PUB),
        'error': context.socket(zmq.PUB),
        'command': context.socket(zmq.PUSH),
        'command_playback': context.socket(zmq.PUSH),
        'command_ripping': context.socket(zmq.PUSH),
        'command_minidisc': context.socket(zmq.PUSH)
    }

    channels['state'].bind(channel_state._pub_addresses[b'ctl'])
    channels['error'].bind(channel_error._pub_addresses[b'ctl'])
    channels['command'].connect(channel_command._address)
    channels['command_playback'].connect(channel_command_playback._address)
    channels['command_ripping'].connect(channel_command_ripping._address)
    channels['command_minidisc'].connect(channel_command_minidisc._address)

    while True:
        (channel, message) = COMMAND_QUEUE.get()
        socket = channels[channel]
        socket.send_multipart([message_part.encode('ascii') for message_part in message])


def simulate_lirc(key):
    if key not in REMOTE_KEYS.keys():
        print('No such remote key registered, known keys are:')
        print(', '.join(REMOTE_KEYS.keys()))
        return

    with lirc.CommandConnection() as conn:
        lirc.SimulateCommand(conn, REMOTE_CONTROL, REMOTE_KEYS[key], 1, 9).run()


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
            if entered[1] in CHANNELS.keys():
                current_channel = entered[1]
            else:
                print('No such channel available. Known channels are:')
                print(', '.join(CHANNELS.keys()))
            continue

        if current_channel == 'lirc':
            simulate_lirc(entered[0])
        else:
            COMMAND_QUEUE.put((current_channel, entered))


if __name__ == '__main__':
    main()
