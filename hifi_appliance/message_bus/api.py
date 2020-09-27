from zmq.eventloop.ioloop import IOLoop

from .util import keys_to_ascii


class Receiver(object):
    """A message receiver for a channel."""

    def __init__(self, channel, name = None, io_loop = None,
                 callbacks = {}, fallback = None, **kw_callbacks):
        """Create a message receiver for a channel, passing received messages
        to callback functions. The callbacks are called with two
        argument:
        callback(receiver, message_parts)
        The first argument is the receiver object.  If event callbacks
        need to interact with the ioloop it should use the
        receiver.io_loop object.
        The second argument is the message parts as returned from
        zqm.socket.recv_multipart().
        RPC message callbacks should return a list of message parts to
        send as a response.
        Callbacks can be defined either in the callbacks dict (if the
        event names contain non-symbol characters) or as key-value
        parameters.  If a name is defined in both places the dict has
        precedence.
        The semantics of the callback names are specific to each kind
        of channel.
        If no callback match and fallback is provided, it is called
        instead.
        """
        self.io_loop = io_loop or IOLoop.instance()
        self.channel = channel
        self.name = name
        callbacks = keys_to_ascii(callbacks)
        self._callbacks = keys_to_ascii(kw_callbacks)
        self._callbacks.update(callbacks)
        self._fallback = fallback
        self._stream = channel.get_receiver_stream(
            iter(callbacks),
            io_loop
        )
        self._stream.on_recv(self._on_message)

    def __str__(self):
        return '<Receiver {0} for {1}>'.format(
            self.name or id(self), str(self.channel))

    def close(self):
        """Close the channel.
        """
        self.io_loop.add_callback(self._do_close)

    def _do_close(self):
        if self._stream:
            self._stream.close()
            self._stream = None

    def _on_message(self, msg_parts):
        """Callback when receiving a message on the channel.  Dispatches the
        message to the matching callback (or callbacks).
        """
        assert len(msg_parts) > 0
        self.channel.dispatch_message(
            self._stream, self._callbacks, self._fallback, self, msg_parts
        )


class Sender(object):
    """An asynchronous message sender to Topic and Queue channels.
    """

    def __init__(self, channel, name = None, io_loop = None):
        """Create a message sender to a channel.
        Topic channels require a sender name to be specified, but it
        is nice to provide a sender name for other channels too.
        """
        self.io_loop = io_loop or IOLoop.instance()
        self.channel = channel
        self.name = name.encode('ascii') if name is not None else None
        self._stream = channel.get_sender_stream(name, io_loop)

    def __str__(self):
        return '<Sender {0} for {1}>'.format(
            self.name or id(self), str(self.channel))

    def send(self, *msg_parts):
        """Send a multipart message to the channel.
        """
        ascii_msg_parts = [self.name] if self.name is not None else []
        ascii_msg_parts += [msg_part.encode('ascii') for msg_part in msg_parts]
        self.io_loop.add_callback(lambda: self._stream.send_multipart(ascii_msg_parts))

    def close(self, linger = None):
        """Close the channel.
        """
        self.io_loop.add_callback(lambda: self._do_close(linger))

    def _do_close(self, linger):
        if self._stream:
            self._stream.close(linger = linger)
            self._stream = None


def setup_command_receiver(obj, channel):
    callbacks = {}
    for name in dir(obj):
        if name.startswith('command_'):
            func = getattr(obj, name)
            if callable(func):
                callbacks[name[8:]] = (
                    lambda receiver, msg, func2 = func: obj.handle_command(msg, func2)
                )

    return Receiver(
        channel,
        io_loop = obj.io_loop,
        callbacks = callbacks,
        fallback = obj.handle_unknown_command
    )
