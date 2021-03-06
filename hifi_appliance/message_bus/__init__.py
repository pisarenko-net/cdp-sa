from .api import Receiver, Sender, setup_command_receiver
from .channel import Queue, Topic


# State changes
state = Topic(
    name='state',
    commander='tcp://127.0.0.1:7921',
    playback='tcp://127.0.0.1:7922',
    ripping='tcp://127.0.0.1:7923',
    ctl='tcp://127.0.0.1:7924'
)


# Errors
error = Topic(
    name='error',
    playback='tcp://127.0.0.1:7932',
    ripping='tcp://127.0.0.1:7933',
    ctl='tcp://127.0.0.1:7934',
)


# Commands, open to user/OS interaction
command = Queue(
    name='command',
    address='tcp://127.0.0.1:7942',
)


# Playback commands, to only be called by commander
command_playback = Queue(
    name='command_playback',
    address='tcp://127.0.0.1:7943',
)


# Ripper commands, to only be called by commander
command_ripping = Queue(
    name='command_ripping',
    address='tcp://127.0.0.1:7963',
)
