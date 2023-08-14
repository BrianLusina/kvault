"""
Entry point to server
"""
import argparse
import importlib
from .queue_server import QueueServer
from .infra.logger import logger


def get_args_parser():
    """
    Options parser. parses the options that will be used on the command line and returns a parser
    """
    parser = argparse.ArgumentParser(prog="KVault", description="Key Value Store")

    parser.add_argument(
        "-d", "--debug", action="store_true", dest="debug", help="Log debug messages."
    )
    parser.add_argument(
        "-e",
        "--errors",
        action="store_true",
        dest="error",
        help="Log error messages only.",
    )
    parser.add_argument(
        "-H", "--host", default="127.0.0.1", dest="host", help="Host to listen on."
    )
    parser.add_argument(
        "-m",
        "--max-clients",
        default=1024,
        dest="max_clients",
        help="Maximum number of clients.",
        type=int,
    )
    parser.add_argument(
        "-p", "--port", default=31337, dest="port", help="Port to listen on.", type=int
    )
    parser.add_argument("-l", "--log-file", dest="log_file", help="Log file.")
    parser.add_argument(
        "-x",
        "--extension",
        action="append",
        dest="extensions",
        help="Import path for Python extension module(s).",
    )
    return parser


def load_extensions(server, extensions):
    """
    Loads extensions that will be added and initialized with the server.
    :param server: Server instance
    :param extensions: list of extensions to load
    :return:
    """
    for extension in extensions:
        try:
            module = importlib.import_module(extension)
        except ImportError:
            logger.exception(f"Could not import extension {extension}")
        else:
            try:
                initialize = getattr(module, "initialize")
            except AttributeError:
                logger.exception(
                    f'Could not find "initialize" function in extension {extension}'
                )
                raise

            initialize(server)
            logger.info(f"Loaded {extension} extension")


if __name__ == "__main__":
    args = get_args_parser().parse_args()

    from gevent import monkey

    monkey.patch_all()

    # configure_logger(options)
    queue_server = QueueServer(
        host=args.host, port=args.port, max_clients=args.max_clients
    )
    load_extensions(queue_server, args.extensions or ())
    print("\x1b[32m  .--.")
    print(
        # pylint: disable-next=consider-using-f-string
        " /( \x1b[34m@\x1b[33m >\x1b[32m    ,-.  "
        "\x1b[1;32mKVault "
        "\x1b[1;33m%s:%s\x1b[32m" % (args.host, args.port)
    )
    print("/ ' .'--._/  /")
    print(":   ,    , .'")
    print("'. (___.'_/")
    print(" \x1b[33m((\x1b[32m-\x1b[33m((\x1b[32m-''\x1b[0m")
    try:
        queue_server.run()
    except KeyboardInterrupt:
        print("\x1b[1;31mshutting down\x1b[0m")
