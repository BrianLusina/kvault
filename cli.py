"""
Entry point to starting the server
"""
import optparse
import importlib
from kvault.queue_server import QueueServer
from kvault.infra.logger import logger


def get_option_parser():
    parser = optparse.OptionParser()
    parser.add_option('-d', '--debug', action='store_true', dest='debug',
                      help='Log debug messages.')
    parser.add_option('-e', '--errors', action='store_true', dest='error',
                      help='Log error messages only.')
    parser.add_option('-H', '--host', default='127.0.0.1', dest='host',
                      help='Host to listen on.')
    parser.add_option('-m', '--max-clients', default=1024, dest='max_clients',
                      help='Maximum number of clients.', type=int)
    parser.add_option('-p', '--port', default=31337, dest='port',
                      help='Port to listen on.', type=int)
    parser.add_option('-l', '--log-file', dest='log_file', help='Log file.')
    parser.add_option('-x', '--extension', action='append', dest='extensions',
                      help='Import path for Python extension module(s).')
    return parser


def load_extensions(server, extensions):
    for extension in extensions:
        try:
            module = importlib.import_module(extension)
        except ImportError:
            logger.exception('Could not import extension %s' % extension)
        else:
            try:
                initialize = getattr(module, 'initialize')
            except AttributeError:
                logger.exception('Could not find "initialize" function in '
                                 'extension %s' % extension)
                raise
            else:
                initialize(server)
                logger.info('Loaded %s extension.' % extension)


if __name__ == '__main__':
    options, args = get_option_parser().parse_args()

    from gevent import monkey

    monkey.patch_all()

    # configure_logger(options)
    server = QueueServer(host=options.host, port=options.port,
                         max_clients=options.max_clients)
    load_extensions(server, options.extensions or ())
    print('\x1b[32m  .--.')
    print(' /( \x1b[34m@\x1b[33m >\x1b[32m    ,-.  '
          '\x1b[1;32mKVault '
          '\x1b[1;33m%s:%s\x1b[32m' % (options.host, options.port))
    print('/ \' .\'--._/  /')
    print(':   ,    , .\'')
    print('\'. (___.\'_/')
    print(' \x1b[33m((\x1b[32m-\x1b[33m((\x1b[32m-\'\'\x1b[0m')
    try:
        server.run()
    except KeyboardInterrupt:
        print('\x1b[1;31mshutting down\x1b[0m')
