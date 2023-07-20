"""
Socket Pool used by the client to manage connections to the server
"""
import heapq
import time
from io import BufferedRWPair
from typing import Dict, List, Tuple, Any, Callable, Union
from gevent import socket
from gevent.thread import get_ident


class SocketPool:
    """
    Manages connections to the kvault server
    """

    # pylint: disable-next=missing-function-docstring
    def __init__(self, host: str, port, max_age: int = 60):
        self.host = host
        self.port = port
        self.max_age = max_age
        self.free: List[Tuple[float, BufferedRWPair]] = []
        self.in_use: Dict[Union[int, BufferedRWPair], BufferedRWPair] = {}
        self._tid: Callable[[Any], int] = get_ident

    # pylint: disable-next=missing-function-docstring
    def checkout(self):
        """Establishes a socket connection"""
        now = time.time()
        tid = self._tid()
        if tid in self.in_use:
            sock = self.in_use[tid]
            if sock.closed:
                del self.in_use[sock]
            else:
                return self.in_use[sock]

        while self.free:
            timestamp, sock = heapq.heappop(self.free)
            if timestamp < now - self.max_age:
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
        """Checks if there is an in use socket connection and adds it to the heap returning a boolean value. True
        indicates that the socket is in use, false indicates it is not"""
        tid = self._tid()
        if tid in self.in_use:
            sock = self.in_use.pop(tid)
            if not sock.closed:
                heapq.heappush(self.free, (time.time(), sock))
            return True
        return False

    def close(self):
        """Closes connection of the socket"""
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
        """Connects to socket on the AF_INET family with the SOCK_STREAM socket kind and returns a BufferedRWPair"""
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        conn.connect((self.host, self.port))
        return conn.makefile("rwb")
