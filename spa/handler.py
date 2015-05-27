from werkzeug.exceptions import MethodNotAllowed, NotImplemented

class Handler(object):
    """Baseclass for our handlers."""

    allowed_methods = ('GET', 'HEAD', 'POST', 'DELETE', 'PUT')

    def __init__(self, app, req, params, **kwargs):
        self.app = app
        self.request = req
        self.params = params

    def get(self):
        raise MethodNotAllowed()
    post = delete = put = websocket = get

    def head(self):
        return self.get()

    def cleanup(self):
        pass

    def __call__(self, environ, start_response):
        if self.request.method not in self.allowed_methods:
            raise NotImplemented()

        if self.request.method == 'GET' and 'wsgi.websocket' in environ:
            self.ws = environ['wsgi.websocket']
            self.ws.add_close_callback(self.cleanup)

            handler = self.websocket
        else:
            handler = getattr(self, self.request.method.lower())

        resp = handler(**self.params)
        return resp(environ, start_response)

