"""
Kvault client that communicates via protocol handler to the server
"""
import logging
from kvault.protocol_handler import ProtocolHandler
from kvault.socket_pool import SocketPool
from kvault.exceptions import ServerDisconnect, ServerInternalError, CommandError, Error

logger = logging.getLogger(__name__)


class Client:
    """
    KCault Client
    """

    def __init__(self, host='127.0.0.1', port=31337, pool_max_age=60):
        self._host = host
        self._port = port
        self._socket_pool = SocketPool(host, port, pool_max_age)
        self._protocol = ProtocolHandler()

    def execute(self, *args):
        """
        Executes a give command
        :param args: Arguments for command
        :return: response from executed command
        """
        conn = self._socket_pool.checkout()
        close_conn = args[0] in (b'QUIT', b'SHUTDOWN')
        self._protocol.write_response(conn, args)
        try:
            resp = self._protocol.handle_request(conn)
        except EOFError as exc:
            self._socket_pool.close()
            raise ServerDisconnect('server went away') from exc
        except Exception as exc:
            self._socket_pool.close()
            raise ServerInternalError('internal server error') from exc
        else:
            if close_conn:
                self._socket_pool.close()
            else:
                self._socket_pool.checkin()
        if isinstance(resp, Error):
            logger.error(f"Received an error {resp.message}")
            raise CommandError(resp.message)
        return resp

    def close(self):
        """
        Closes client connection
        """
        self.execute(b'QUIT')

    @staticmethod
    def command(cmd):
        """
        Parses a command executes the given command.
        :param cmd: Command name
        :return: handler method
        """

        def method(self, *args):
            return self.execute(cmd.encode('utf-8'), *args)

        return method

    lpush = command(cmd='LPUSH')
    rpush = command(cmd='RPUSH')
    lpop = command(cmd='LPOP')
    rpop = command(cmd='RPOP')
    lrem = command(cmd='LREM')
    llen = command(cmd='LLEN')
    lindex = command(cmd='LINDEX')
    lrange = command(cmd='LRANGE')
    lset = command(cmd='LSET')
    ltrim = command(cmd='LTRIM')
    rpoplpush = command(cmd='RPOPLPUSH')
    lflush = command(cmd='LFLUSH')

    append = command(cmd='APPEND')
    decr = command(cmd='DECR')
    decrby = command(cmd='DECRBY')
    delete = command(cmd='DELETE')
    exists = command(cmd='EXISTS')
    get = command(cmd='GET')
    getset = command(cmd='GETSET')
    incr = command(cmd='INCR')
    incrby = command(cmd='INCRBY')
    mdelete = command(cmd='MDELETE')
    mget = command(cmd='MGET')
    mpop = command(cmd='MPOP')
    mset = command(cmd='MSET')
    msetex = command(cmd='MSETEX')
    pop = command(cmd='POP')
    set = command(cmd='SET')
    setex = command(cmd='SETEX')
    setnx = command(cmd='SETNX')
    length = command(cmd='LEN')
    flush = command(cmd='FLUSH')

    hdel = command(cmd='HDEL')
    hexists = command(cmd='HEXISTS')
    hget = command(cmd='HGET')
    hgetall = command(cmd='HGETALL')
    hincrby = command(cmd='HINCRBY')
    hkeys = command(cmd='HKEYS')
    hlen = command(cmd='HLEN')
    hmget = command(cmd='HMGET')
    hmset = command(cmd='HMSET')
    hset = command(cmd='HSET')
    hsetnx = command(cmd='HSETNX')
    hvals = command(cmd='HVALS')

    sadd = command(cmd='SADD')
    scard = command(cmd='SCARD')
    sdiff = command(cmd='SDIFF')
    sdiffstore = command(cmd='SDIFFSTORE')
    sinter = command(cmd='SINTER')
    sinterstore = command(cmd='SINTERSTORE')
    sismember = command(cmd='SISMEMBER')
    smembers = command(cmd='SMEMBERS')
    spop = command(cmd='SPOP')
    srem = command(cmd='SREM')
    sunion = command(cmd='SUNION')
    sunionstore = command(cmd='SUNIONSTORE')

    add = command(cmd='ADD')
    read = command(cmd='READ')
    flush_schedule = command(cmd='FLUSH_SCHEDULE')
    length_schedule = command(cmd='LENGTH_SCHEDULE')

    expire = command(cmd='EXPIRE')
    info = command(cmd='INFO')
    flushall = command(cmd='FLUSHALL')
    save = command(cmd='SAVE')
    restore = command(cmd='RESTORE')
    merge = command(cmd='MERGE')
    quit = command(cmd='QUIT')
    shutdown = command(cmd='SHUTDOWN')

    def __getitem__(self, key):
        if isinstance(key, (list, tuple)):
            return self.mget(*key)
        else:
            return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def __contains__(self, key):
        return self.exists(key)

    def __len__(self):
        return self.length()
