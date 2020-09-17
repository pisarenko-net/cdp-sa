import zmq


_context = None
def get_zmq_context():
    global _context
    if _context is None:
        _context = zmq.Context()
    return _context

