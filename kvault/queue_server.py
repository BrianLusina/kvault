"""
KVault server that is used by the clients to send commands. The QueueServer has the same implementation of the protocol
handler that clients use to parse and send commands. The queue server uses the protocol handler to serialize &
deserialize the messages
"""
from typing import Dict, Callable, AnyStr, Union, Any, List, Tuple
from dataclasses import dataclass, field
import time
from io import BufferedRWPair
from gevent.pool import Pool
from gevent.server import StreamServer
from kvault.infra.logger import logger
from .exceptions import ClientQuit, Shutdown, CommandError, Error
from .protocol_handler import ProtocolHandler
from .types import basestring, Value, unicode
from .utils.mixins import MetaUtils
from .commands import Commands


@dataclass
class Counter:
    """
    Counter contains the counts tracked by the QueueServer.
    :cvar active_connections is the number of current active connections to the queue server
    :cvar commands_processed is the number of commands that the server has processed
    :cvar command_errors is the count of errors encountered by the server
    :cvar connections is the number of connections to the server
    """

    active_connections: int = 0
    commands_processed: int = 0
    command_errors: int = 0
    connections: int = 0


@dataclass
class ServerInfo:
    """
    Counter contains the Server information
    :cvar host is the host the server will run on
    :cvar port is the port the server will run on
    :cvar max_clients is the maximum number of clients that the server will accept connections from
    """

    host: str = "127.0.0.1"
    port: int = 31337
    max_clients: int = 1024


@dataclass
class ServerState:
    """
    Contains the server state
    :cvar kv_store is the in memory Key Value store
    :cvar schedule contains a list of tuples of scheduled commands
    :cvar expiry
    :cvar expiry_map a key value pair where the key is the expiry time and the value is the value. This contains the
    expired data
    """

    kv_store: Dict[AnyStr, Value] = field(default_factory=dict)
    schedule: List[Tuple[Any, Any]] = field(default_factory=list)
    expiry: List[Tuple[float, Any]] = field(default_factory=list)
    expiry_map: Dict[Any, float] = field(default_factory=dict)


class QueueServer(Commands, MetaUtils):
    """
    Queue Server where server send commands to
    """

    # pylint: disable-next=missing-function-docstring
    def __init__(
        self, host: str = "127.0.0.1", port: int = 31337, max_clients: int = 1024
    ):
        self._server_info = ServerInfo(host=host, port=port, max_clients=max_clients)

        self._pool = Pool(max_clients)
        self._server = StreamServer(
            listener=(self._server_info.host, self._server_info.port),
            handle=self.connection_handler,
            spawn=self._pool,
        )
        self._commands = self.get_commands()
        self._protocol = ProtocolHandler()

        self._server_state = ServerState(
            kv_store={}, schedule=[], expiry=[], expiry_map={}
        )

        self._counter = Counter(
            active_connections=0, commands_processed=0, command_errors=0, connections=0
        )

        super().__init__(
            kv_store=self._server_state.kv_store,
            expiry_map=self._server_state.expiry_map,
            expiry=self._server_state.expiry,
            schedule=self._server_state.schedule,
        )

    def connection_handler(self, conn, address):
        """
        Handles a connection given a connection file like object and address
        :param conn: File like socket object
        :param address: address to handle connection on
        """
        logger.info(f"[{self.name}] Connection received: {address}")
        socket_file = conn.makefile("rwb")
        self._counter.active_connections += 1
        while True:
            try:
                self.request_response(socket_file)
            except EOFError:
                logger.info(f"Client went away: {address}")
                socket_file.close()
                break
            except ClientQuit:
                logger.info(f"Client exited: {address}")
                break
            # pylint: disable-next=broad-exception-caught
            except Exception as exc:
                logger.exception(f"Error processing command: {exc}", exc)
        self._counter.active_connections -= 1

    def request_response(self, socket_file: BufferedRWPair):
        """
        Handles the request from a socket file and responds on the protocol handler
        :param socket_file: File like object
        """
        data = self._protocol.handle_request(socket_file)
        try:
            resp = self.respond(data)
        except Shutdown as exc:
            logger.info(f"[{self.name}] Shutting down...")
            self._protocol.write_response(socket_file=socket_file, data=1)
            raise KeyboardInterrupt from exc
        except ClientQuit:
            self._protocol.write_response(socket_file=socket_file, data=1)
            raise
        except CommandError as cmd_error:
            resp = Error(cmd_error.message)
            self._counter.command_errors += 1
        # pylint: disable-next=broad-exception-caught
        except Exception as err:
            logger.error(f"[{self.name}] Unhanded Exception {err}")
            resp = Error(f"Unhandled server error: {err}")
        else:
            self._counter.commands_processed += 1
        self._protocol.write_response(socket_file=socket_file, data=resp)

    def respond(self, data):
        """
        Responds to a given command with the given data. The data is split into 2 parts, the first part is the command
        the second is the data.
        :param data: data to respond to
        :return: response from callback
        """
        if isinstance(data, str):
            try:
                data = data.split()
            # pylint: disable-next=broad-exception-caught
            except Exception as exc:
                raise CommandError(f"Unrecognized request type {data}") from exc
        if not isinstance(data[0], basestring):
            raise CommandError(
                f"First parameter must be command name. Received {data[0]}"
            )

        command = data[0].upper()
        if command not in self._commands:
            logger.error(f"{self.name} Unrecognized command: {command}")
            raise CommandError(f"Unrecognized command: {command}")

        return self._commands[command](*data[1:])

    def get_commands(self) -> Dict[Union[bytes, str], Callable]:
        """
        Returns a mapping of commands to handlers
        :return: Dictionary of commands to handlers
        """
        return dict(
            (
                # Queue commands
                (b"LPUSH", self.lpush),
                (b"RPUSH", self.rpush),
                (b"LPOP", self.lpop),
                (b"RPOP", self.rpop),
                (b"LREM", self.lrem),
                (b"LLEN", self.llen),
                (b"LINDEX", self.lindex),
                (b"LRANGE", self.lrange),
                (b"LSET", self.lset),
                (b"LTRIM", self.ltrim),
                (b"RPOPLPUSH", self.rpoplpush),
                (b"LFLUSH", self.lflush),
                # K/V commands
                (b"APPEND", self.kv_append),
                (b"DECR", self.kv_decr),
                (b"DECRBY", self.kv_decrby),
                (b"DELETE", self.kv_delete),
                (b"EXISTS", self.kv_exists),
                (b"GET", self.kv_get),
                (b"GETSET", self.kv_getset),
                (b"INCR", self.kv_incr),
                (b"INCRBY", self.kv_incrby),
                (b"MDELETE", self.kv_mdelete),
                (b"MGET", self.kv_mget),
                (b"MPOP", self.kv_mpop),
                (b"MSET", self.kv_mset),
                (b"MSETEX", self.kv_msetex),
                (b"POP", self.kv_pop),
                (b"SET", self.kv_set),
                (b"SETNX", self.kv_setnx),
                (b"SETEX", self.kv_setex),
                (b"LEN", self.kv_len),
                (b"FLUSH", self.kv_flush),
                # Hash commands.
                (b"HDEL", self.hdel),
                (b"HEXISTS", self.hexists),
                (b"HGET", self.hget),
                (b"HGETALL", self.hgetall),
                (b"HINCRBY", self.hincrby),
                (b"HKEYS", self.hkeys),
                (b"HLEN", self.hlen),
                (b"HMGET", self.hmget),
                (b"HMSET", self.hmset),
                (b"HSET", self.hset),
                (b"HSETNX", self.hsetnx),
                (b"HVALS", self.hvals),
                # Set commands.
                (b"SADD", self.sadd),
                (b"SCARD", self.scard),
                (b"SDIFF", self.sdiff),
                (b"SDIFFSTORE", self.sdiffstore),
                (b"SINTER", self.sinter),
                (b"SINTERSTORE", self.sinterstore),
                (b"SISMEMBER", self.sismember),
                (b"SMEMBERS", self.smembers),
                (b"SPOP", self.spop),
                (b"SREM", self.srem),
                (b"SUNION", self.sunion),
                (b"SUNIONSTORE", self.sunionstore),
                # Schedule commands.
                (b"ADD", self.schedule_add),
                (b"READ", self.schedule_read),
                (b"FLUSH_SCHEDULE", self.schedule_flush),
                (b"LENGTH_SCHEDULE", self.schedule_length),
                # Misc.
                (b"EXPIRE", self.expire),
                (b"INFO", self.info),
                (b"FLUSHALL", self.flush_all),
                (b"SAVE", self.save_to_disk),
                (b"RESTORE", self.restore_from_disk),
                (b"MERGE", self.merge_from_disk),
                (b"QUIT", self.client_quit),
                (b"SHUTDOWN", self.shutdown),
            )
        )

    def info(self) -> Dict:
        """
        Retrieves the current information of the server
        :return: dictionary mapping of the server information
        """
        return {
            "active_connections": self._counter.active_connections,
            "commands_processed": self._counter.commands_processed,
            "command_errors": self._counter.command_errors,
            "connections": self._counter.connections,
            "keys": len(self._kv),
            "timestamp": time.time(),
        }

    def flush_all(self):
        """
        Clears the store and scheduled commands
        :return: 1 once flushing is successful
        """
        self.kv_flush()
        self.schedule_flush()
        return 1

    def run(self):
        """
        Runs and starts the server
        """
        self._server.serve_forever()

    def add_command(self, command, callback):
        """
        Adds a command to the list of commands supported by the server
        :param command: command name
        :param callback: callback to handle command
        """
        if isinstance(command, unicode):
            command = command.encode("utf-8")
        self._commands[command] = callback
