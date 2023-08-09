"""
Exception types
"""
from collections import namedtuple


class CommandError(Exception):
    """
    Command error exception raised when there is an error with a command
    """

    def __init__(self, message):
        """
        Creates an instance of a command error with a given message.
        :param message: Message of exception
        """
        self.message = message
        super().__init__(message)


class ClientQuit(Exception):
    """Raised when a client quits a connection to the server"""


class Shutdown(Exception):
    """Raised when a there is a shutdown command"""


class ServerError(Exception):
    """Raised when a there is a server error"""


class ServerDisconnect(ServerError):
    """Raised when a there is a server disconnect from the connection pool"""


class ServerInternalError(ServerError):
    """Raised when a there is an internal server error"""


Error = namedtuple("Error", ("message",))
