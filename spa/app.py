from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule

from spa.wrappers import Request


class App(object):
    def __init__(self, urls, settings=None, request_class=None):
        self.urls = urls
        self.settings = settings
        self.map, self.handlers = build_rules(urls)
        self.request_class = request_class or Request

    def __call__(self, environ, start_response):
        try:
            wsgi_app = self.get_handler(environ)
            resp = wsgi_app(environ, start_response)
        except HTTPException as e:
            wsgi_app = e
            resp = wsgi_app(environ, start_response)

        return resp

    def get_handler(self, environ):
        req = self.request_class(environ)
        adapter = self.map.bind_to_environ(environ)
        route_name, params = adapter.match()
        cls, kwargs = self.handlers[route_name]
        return cls(self, req, params, route_name, **kwargs)

    def url(self, endpoint, **values):
        return self.map.bind('').build(endpoint, values=values)


def build_rules(rules_tuples):
    handlers = {}
    rules = []
    for pat, name, handler, kwargs in [tuple_to_rule(t) for t in rules_tuples]:
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
