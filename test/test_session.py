from __future__ import print_function

import datetime

from werkzeug.test import Client
import jwt
import pytest
import utc

import spa
from spa.jwtcookie import JWTSessionMiddleware, JWTSessionParamMiddleware

def test_read_session_cookie():
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
    assert resp.data == b'bar'


def test_write_session_cookie():
    class A(spa.Handler):
        def get(self):
            self.request.environ['jwtsession']['foo'] = 'bar'
            return spa.Response()

    routes = (
        ('/', 'a', A),
    )

    app = spa.App(routes)

    secret = 'foobar'

    app = JWTSessionMiddleware(app, secret_key=secret)

    c = Client(app, spa.Response)
    c.get('/')
    cookie = next(ck for ck in c.cookie_jar if ck.name=='session')
    session = jwt.decode(cookie.value, secret)
    assert session['foo'] == 'bar'


def test_exclude_path():
    class A(spa.Handler):
        def get(self, blah):
            return spa.Response(blah)

    routes = (
        ('/foo/<blah>/', 'a', A),
        ('/bar/<blah>/', 'a', A),
    )

    app = spa.App(routes)

    secret = 'foobar'

    app = JWTSessionMiddleware(
        app,
        secret_key=secret,
        exclude_pattern='^/foo/*',
    )

    c = Client(app, spa.Response)
    resp = c.get('/foo/bazquux/')
    assert 'Set-Cookie' not in resp.headers
    assert 'session' not in {ck.name for ck in c.cookie_jar}

    resp = c.get('/bar/bazquux/')
    assert 'Set-Cookie' in resp.headers
    assert 'session' in {ck.name for ck in c.cookie_jar}


def test_qs_middleware():
    class A(spa.Handler):
        def get(self):
            session = self.request.environ['jwtsession']
            assert 'foo' in session
            return spa.Response(session['foo'])

    routes = (
        ('/', 'a', A),
    )

    app = spa.App(routes)

    secret = 'foobar'

    app = JWTSessionParamMiddleware(app, secret_key=secret)
    app = JWTSessionMiddleware(app, secret_key=secret)

    c = Client(app, spa.Response)
    token = jwt.encode({'foo': 'bar', 'iat': utc.now()}, secret).decode('utf-8')
    url = '/?session_token=%s' % token
    resp = c.get(url)
    assert resp.data == b'bar'
    cookieparts = resp.headers['Set-Cookie'].split('; ')[0].split('=')
    assert cookieparts[0] == 'session'
    assert jwt.decode(cookieparts[1], secret)['foo'] == 'bar'


def test_jwtsession_expire_days():
    class A(spa.Handler):
        def get(self):
            return spa.Response(self.request.environ['jwtsession']['foo'])

    routes = (
        ('/', 'a', A),
    )

    app = spa.App(routes)

    secret = 'foobar'

    app = JWTSessionMiddleware(app, secret_key=secret, expire_days=1)

    c = Client(app, spa.Response)
    tok = jwt.encode({
        'foo': 'bar',
        'iat': utc.now() - datetime.timedelta(days=1)
    }, secret)
    c.set_cookie('localhost', 'session', tok)
    with pytest.raises(KeyError):
        # The handler should fail to read 'foo' from the session, because it
        # will have been dropped when the middleware saw that its 'iat'
        # timestamp was too old.
        c.get('/')
