from __future__ import print_function

from werkzeug.test import Client
import jwt
import utc

import spa
from spa.jwtcookie import JWTSessionMiddleware, JWTSessionParamMiddleware

def test_session_cookie():
    class A(spa.Handler):
        def get(self):
            return spa.Response(self.request.environ['jwtsession']['foo'])

    routes = (
        ('/', 'a', A),
    )

    app = spa.App(routes)

    secret = 'foobar'

    app = JWTSessionMiddleware(app, secret_key=secret)

    c = Client(app, spa.Response)
    c.set_cookie('localhost', 'session', jwt.encode({'foo': 'bar',
                                                     'iat': utc.now()}, secret))
    resp = c.get('/')
    assert resp.data == 'bar'


def test_qs_middleware():
    class A(spa.Handler):
        def get(self):
            return spa.Response(self.request.environ['jwtsession']['foo'])

    routes = (
        ('/', 'a', A),
    )

    app = spa.App(routes)

    secret = 'foobar'

    app = JWTSessionParamMiddleware(app, secret_key=secret)
    app = JWTSessionMiddleware(app, secret_key=secret)

    c = Client(app, spa.Response)
    resp = c.get('/?session_token=%s' % jwt.encode({'foo': 'bar',
                                                    'iat': utc.now()}, secret))
    assert resp.data == 'bar'
    cookieparts = resp.headers['Set-Cookie'].split('; ')[0].split('=')
    assert cookieparts[0] == 'session'
    assert jwt.decode(cookieparts[1], secret)['foo'] == 'bar'

