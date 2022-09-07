from collections import namedtuple


class CommandError(Exception):
    def __init__(self, message):
        self.message = message
        super(CommandError, self).__init__()


class ClientQuit(Exception):
    pass


class Shutdown(Exception):
    pass


class ServerError(Exception):
    pass


class ServerDisconnect(ServerError):
    pass


class ServerInternalError(ServerError):
    pass


Error = namedtuple("Error", ("message",))
