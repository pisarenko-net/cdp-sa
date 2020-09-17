import zmq
from zmq.eventloop.zmqstream import ZMQStream

from .context import get_zmq_context
from .util import decode_list_to_str
from .util import keys_to_ascii


class UndefinedSenderError(Exception):
    pass


class Channel(object):
    """Common message channel interface for the specific kinds of channels
    defined as subclasses.
    """

    def get_receiver_stream(self, subscriptions, io_loop = None):
        """Return a ZMQStream for receiving messages from this channel.
        subscriptions is an iterable of event names that the stream
        should subscribe to (if applicable).
        """
        raise NotImplementedError()

    def get_sender_stream(self, name, io_loop = None):
        """Return a ZMQStream for sending messages to this channel
        for a named sender.
        """
        raise NotImplementedError()

    def dispatch_message(self, stream, callbacks, fallback, receiver, msg_parts):
        """Dispatch a received message to the correct callback or callbacks,
        using the channel semantics.
        """
        raise NotImplementedError()


class Topic(Channel):
    """An event topic supporting any number of publishers and subscribers.
    """
    def __init__(self, name = None, **pub_addresses):
        """Define a topic, listing all the publishers and the ZeroMQ socket
        address of each as key-value pairs.
        MessageHandler event names have the same semantics as ZeroMQ
        PUB/SUB sockets, i.e. they match if the name of the received
        event starts with the same sequence of characters.
        """
        self.name = name.encode('ascii')
        self._pub_addresses = keys_to_ascii(pub_addresses)

    def __str__(self):
        return '<Topic {0} on {1}>'.format(
            self.name or id(self),
            ', '.join(['{}={}'.format(k, v)
                       for k, v
                       in self._pub_addresses.items()]))

    def get_receiver_stream(self, subscriptions, io_loop = None):
        """Return a SUB socket stream.
        """
        socket = get_zmq_context().socket(zmq.SUB)
        socket.set_hwm(10)

        for address in self._pub_addresses.values():
            socket.connect(address)

        for sub in subscriptions:
            socket.set(zmq.SUBSCRIBE, sub)

        return ZMQStream(socket, io_loop)

    def get_sender_stream(self, name, io_loop = None):
        """Return a PUB socket stream.
        """
        try:
            address = self._pub_addresses[name.encode('ascii')]
        except KeyError:
            raise UndefinedSenderError(name)

        socket = get_zmq_context().socket(zmq.PUB)
        socket.set_hwm(10)
        socket.bind(address)

        return ZMQStream(socket, io_loop)

    def dispatch_message(self, stream, callbacks, fallback, receiver, msg_parts):
        """Send messages to all the callbacks matching a prefix of the message name.
        """

        decoded_msg_parts = decode_list_to_str(msg_parts)
        msg_name = decoded_msg_parts[0]

        for sub, func in callbacks.items():
            if msg_name.startswith(sub.decode('ascii')):
                fallback = None
                func(receiver, msg_parts)

        if fallback:
            fallback(receiver, msg_parts)


class Queue(Channel):
    """A one-way queue where any number of clients can send messages
    (typically commands) to a single service.
    """
    def __init__(self, address, name = None):
        """Define a one-way queue, listening on address.
        MessageHandler event names must match the received event name
        exactly to invoke a callback.
        """
        self.name = name.encode('ascii')
        self._address = address

    def __str__(self):
        return '<Queue {0} on {1}>'.format(self.name or id(self), self._address)

    def get_receiver_stream(self, subscriptions, io_loop = None):
        """Return a PULL socket stream.
        """
        socket = get_zmq_context().socket(zmq.PULL)
        socket.bind(self._address)
        return ZMQStream(socket, io_loop)

    def get_sender_stream(self, name, io_loop = None):
        """Return a PUSH socket stream.
        """
        socket = get_zmq_context().socket(zmq.PUSH)
        socket.connect(self._address)
        return ZMQStream(socket, io_loop)

    def dispatch_message(self, stream, callbacks, fallback, receiver, msg_parts):
        """Send messages to all the callbacks matching a prefix of the message name.
        """
        func = callbacks.get(msg_parts[0], fallback)
        if func:
            func(receiver, msg_parts)
