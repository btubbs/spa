from werkzeug.test import Client

import spa
from spa.middlewares import ApiCSRFMiddleware


def test_csrf_cookie_set():
    class A(spa.Handler):
        def get(self):
            return spa.Response('hello world')

    routes = (
        ('/', 'a', A),
    )

    app = ApiCSRFMiddleware(spa.App(routes))
    c = Client(app, spa.Response)
    resp = c.get('/')
    assert resp.status_code == 200
    cookie = next(ck for ck in c.cookie_jar if ck.name=='api_csrf')
    assert cookie.value


def test_matched_tokens_allowed():
    class A(spa.Handler):
        def post(self):
            return spa.Response('hello world')
    routes = (
        ('/', 'a', A),
    )

    app = ApiCSRFMiddleware(spa.App(routes))
    c = Client(app, spa.Response)
    c.set_cookie('localhost', 'api_csrf', 'foobar')
    resp = c.post('/', headers={'X-Api-CSRF': 'foobar'})
    assert resp.status_code == 200


def test_empty_cookie_blocked():
    class A(spa.Handler):
        def post(self):
            return spa.Response('hello world')
    routes = (
        ('/', 'a', A),
    )

    app = ApiCSRFMiddleware(spa.App(routes))
    c = Client(app, spa.Response)
    resp = c.post('/', headers={'X-Api-CSRF': 'foobar'})
    assert resp.status_code == 403


def test_mismatched_tokens_blocked():
    class A(spa.Handler):
        def post(self):
            return spa.Response('hello world')
    routes = (
        ('/', 'a', A),
    )

    app = ApiCSRFMiddleware(spa.App(routes))
    c = Client(app, spa.Response)
    c.set_cookie('localhost', 'api_csrf', 'foobar')
    resp = c.post('/', headers={'X-Api-CSRF': 'barfoo'})
    assert resp.status_code == 403


def test_empty_header_blocked():
    class A(spa.Handler):
        def post(self):
            return spa.Response('hello world')
    routes = (
        ('/', 'a', A),
    )

    app = ApiCSRFMiddleware(spa.App(routes))
    c = Client(app, spa.Response)
    c.set_cookie('localhost', 'api_csrf', 'foobar')
    resp = c.post('/')
    assert resp.status_code == 403


def test_exclude_pattern():
    class A(spa.Handler):
        def post(self):
            return spa.Response('hello world')
    routes = (
        ('/unblocked', 'unblocked', A),
        ('/blocked', 'blocked', A),
    )

    app = ApiCSRFMiddleware(
        spa.App(routes),
        exclude_pattern='/unblocked'
    )
    c = Client(app, spa.Response)
    resp = c.post('/blocked')
    assert resp.status_code == 403
    resp = c.post('/unblocked')
    assert resp.status_code == 200
