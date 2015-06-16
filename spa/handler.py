from werkzeug.exceptions import MethodNotAllowed

class Handler(object):
    """Baseclass for our handlers."""

    allowed_methods = ('GET', 'HEAD', 'POST', 'DELETE', 'PUT')

    def __init__(self, app, req, params, **kwargs):
        self.app = app
        self.request = req
        self.params = params

    def get(self):
        return MethodNotAllowed()
    post = delete = put = websocket = get

    def head(self):
        return self.get()

    def websocket_close(self):
        pass

    def __call__(self, environ, start_response):
        if self.request.method not in self.allowed_methods:
            return MethodNotAllowed()(environ, start_response)

        if self.request.method == 'GET' and 'wsgi.websocket' in environ:
            self.ws = environ['wsgi.websocket']
            self.ws.add_close_callback(self.websocket_close)

            handler = self.websocket
        else:
            handler = getattr(self, self.request.method.lower())

        resp = handler(**self.params)
        return resp(environ, start_response)

