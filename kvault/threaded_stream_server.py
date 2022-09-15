import socketserver


class ThreadedStreamServer(object):
    def __init__(self, address, handler):
        self.stream_server = None
        self.address = address
        self.handler = handler

    def serve_forever(self):
        handler = self.handler

        class RequestHandler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                return handler(self.request, self.client_address)

        class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
            allow_reuse_port = True

        self.stream_server = ThreadedServer(self.address, RequestHandler)
        self.stream_server.serve_forever()

    def stop(self):
        if self.stream_server:
            self.stream_server.shutdown()
