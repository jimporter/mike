from io import BytesIO


class MockRequest:
    class LoggingBytesIO(BytesIO):
        def __init__(self, parent):
            BytesIO.__init__(self)
            self.parent = parent

        def close(self):
            self.parent.response = self.getvalue()
            BytesIO.close(self)

    def __init__(self, method=b'GET', path=b'/'):
        self.method = method
        self.path = path

    def makefile(self, mode, size):
        if 'r' in mode:
            return BytesIO(self.method + b' ' + self.path + b' HTTP/1.1')
        else:
            return self.LoggingBytesIO(self)


class MockServer:
    def __init__(self, addr, handler):
        self.addr = addr
        self.handler = handler

    def handle_request(self, request):
        self.handler(request, self.addr, self)
