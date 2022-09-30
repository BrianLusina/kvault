import heapq
import time
from gevent import socket
from gevent.thread import get_ident


class SocketPool(object):
    def __init__(self, host: str, port, max_age: int = 60):
        self.host = host
        self.port = port
        self.max_age = max_age
        self.free = []
        self.in_use = {}
        self._tid = get_ident

    def checkout(self):
        now = time.time()
        tid = self._tid()
        if tid in self.in_use:
            sock = self.in_use[tid]
            if sock.closed:
                del self.in_use[sock]
            else:
                return self.in_use[sock]

        while self.free:
            ts, sock = heapq.heappop(self.free)
            if ts < now - self.max_age:
                try:
                    sock.close()
                except OSError:
                    pass
            else:
                self.in_use[tid] = sock
                return sock

        sock = self.create_socket_file()
        self.in_use[tid] = sock
        return sock

    def checkin(self):
        tid = self._tid()
        if tid in self.in_use:
            sock = self.in_use.pop(tid)
            if not sock.closed:
                heapq.heappush(self.free, (time.time(), sock))
            return True
        return False

    def close(self):
        tid = self._tid()
        sock = self.in_use.pop(tid, None)
        if sock:
            try:
                sock.close()
            except OSError:
                pass
            return True
        return False

    def create_socket_file(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        conn.connect((self.host, self.port))
        return conn.makefile("rwb")
