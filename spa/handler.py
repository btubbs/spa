from __future__ import print_function

from werkzeug.exceptions import MethodNotAllowed

from spa.wrappers import JSONResponse

class Handler(object):
    """Baseclass for our handlers."""

    allowed_methods = ('GET', 'HEAD', 'POST', 'DELETE', 'PUT', 'PATCH')
    get = post = delete = put = patch = NotImplemented

    def __init__(self, app, req, params, route_name, **kwargs):
        self.app = app
        self.request = req
        self.params = params
        self.route_name = route_name
        self.kwargs = kwargs

    def head(self, *args, **kwargs):
        return self.get()

    def websocket_close(self):
        pass

    def _get_handler(self):
        environ = self.request.environ
        if self.request.method == 'GET' and 'wsgi.websocket' in environ:
            self.ws = environ['wsgi.websocket']
            self.ws.add_close_callback(self.websocket_close)

            return self.websocket
        return getattr(self, self.request.method.lower())

    def _get_response(self, environ, start_response):
        if self.request.method not in self.allowed_methods:
            return MethodNotAllowed()(environ, start_response)

        handler = self._get_handler()

        if handler == NotImplemented:
            return MethodNotAllowed()

        return handler(**self.params)

    def __call__(self, environ, start_response):
        resp = self._get_response(environ, start_response)
        return resp(environ, start_response)


class JSONHandler(Handler):
    """Works the same as Handler, but allows you to reply with just a dict that
    will then be turned into a JSONResponse for you."""


    def __call__(self, environ, start_response):
        resp = self._get_response(environ, start_response)

        if isinstance(resp, dict):
            resp = JSONResponse(resp)
        return resp(environ, start_response)
