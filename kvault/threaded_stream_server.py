"""
Threaded stream server
"""
import socketserver


class ThreadedStreamServer:
    """
    Stream server
    """

    def __init__(self, address, handler):
        self.stream_server = None
        self.address = address
        self.handler = handler

    def serve_forever(self):
        """
        Serves the server forever
        """
        handler = self.handler

        class RequestHandler(socketserver.BaseRequestHandler):
            """
            Request handler
            """

            def handle(self) -> None:
                """
                Handles incoming requests
                :return:
                """
                return handler(self.request, self.client_address)

        class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
            """
            Threaded server
            """

            allow_reuse_port = True

        self.stream_server = ThreadedServer(self.address, RequestHandler)
        self.stream_server.serve_forever()

    def stop(self):
        """
        Stops the running server if available
        """
        if self.stream_server:
            self.stream_server.shutdown()
