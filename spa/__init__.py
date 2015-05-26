import json
import logging

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import BaseRequest, BaseResponse
from werkzeug.exceptions import (HTTPException, MethodNotAllowed,
                                 NotImplemented, NotFound)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class JSONResponse(BaseResponse):
    def __init__(self, data, *args, **kwargs):
        kwargs['content_type'] = 'application/json'
        return super(JSONResponse, self).__init__(json.dumps(data), *args, **kwargs)


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


def build_rules(rules_tuples):
    handlers = {}
    rules = []
    for pat, name, handler, kwargs in [tuple_to_rule(t) for r in rules_tuples]:
        rules.append(Rule(pat, endpoint=name))
        handlers[name] = handler, kwargs
    return Map(rules), handlers


def tuple_to_rule(tpl):
    pat, name, handler = tpl[0], tpl[1], tpl[2]
    if len(tpl) > 3:
        kwargs = tpl[3]
    else:
        kwargs = {}
    return pat, name, handler, kwargs


def reverse(rule_map, endpoint, values=None):
    """ Given a rule map, and the name of one of our endpoints, and a dict of
    parameter values, return a URL"""
    adapter = rule_map.bind('')
    return adapter.build(endpoint, values=values)
