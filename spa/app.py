from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import BaseRequest
from spa.urls import build_rules

class App(object):
    def __init__(self, urls, settings):
        self.urls = urls
        self.settings = settings
        self.map, self.handlers = build_rules(urls)

    def __call__(self, environ, start_response):
        req = BaseRequest(environ)
        try:
            adapter = self.map.bind_to_environ(environ)
            handler_name, params = adapter.match()
            cls, kwargs = self.handlers[handler_name]
            wsgi_app = cls(self, req, params, **kwargs)
        except HTTPException, e:
            wsgi_app = e

        resp = wsgi_app(environ, start_response)

        return resp
