from werkzeug.exceptions import MethodNotAllowed

from spa.wrappers import JSONResponse

class Handler(object):
    """Baseclass for our handlers."""

    allowed_methods = ('GET', 'HEAD', 'POST', 'DELETE', 'PUT')

    def __init__(self, app, req, params, **kwargs):
        self.app = app
        self.request = req
        self.params = params

    def get(self, *args, **kwargs):
        return MethodNotAllowed()
    post = delete = put = websocket = get

    def head(self, *args, **kwargs):
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


class JSONHandler(Handler):
    """Works the same as Handler, but allows you to reply with just a dict that
    will then be turned into a JSONResponse for you."""

    def _get_response(self):
        environ = self.request.environ

        if self.request.method == 'GET' and 'wsgi.websocket' in environ:
            self.ws = environ['wsgi.websocket']
            self.ws.add_close_callback(self.websocket_close)

            handler = self.websocket
        else:
            handler = getattr(self, self.request.method.lower())

        resp = handler(**self.params)

        if isinstance(resp, dict):
            resp = JSONResponse(resp)
        return resp

    def __call__(self, environ, start_response):
        if self.request.method not in self.allowed_methods:
            return MethodNotAllowed()(environ, start_response)
        return self._get_response()(environ, start_response)
