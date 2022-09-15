import gevent
from gevent.thread import get_ident


class SocketPool(object):
    def __init__(self, host: str, port, max_age: int = 60):
        self.host = host
        self.port = port
        self.max_age = max_age
        self.free = []
        self.in_use = {}
        self._tid = get_ident
