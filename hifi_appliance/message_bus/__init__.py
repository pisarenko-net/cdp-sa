from .api import Receiver, Sender
from .channel import Queue, Topic


# State changes
state = Topic(
    name = 'state',
    player = 'tcp://127.0.0.1:7922',
    ripper = 'tcp://127.0.0.1:7923',
)


# Errors
error = Topic(
    name = 'error',
    player = 'tcp://127.0.0.1:7932',
    ripper = 'tcp://127.0.0.1:7933',
)


# CD commands without any response
cd_command = Queue(
    name = 'command',
    address = 'tcp://127.0.0.1:7942',
)

