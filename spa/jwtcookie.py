# -*- coding: utf-8 -*-

r"""
    spa.jwtcookie
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Based on werkzeug.contrib.securecookie, but serialized cookies are JSON Web
    Tokens.

    A cookie serialized as a JSON Web Token can be easily parsed and used in
    client side code.  This means that you can access session data from
    javascript without a round trip to the server.  The big caveat is that
    your client side javascript should not have access to the secret key used to
    sign the token.  Two important implications of this:

        1. Client side javascript cannot verify that the session data has not
        been tampered with.  It must trust it blindly.
        2. Client side javascript cannot set new values in the session.

    The primary use case is to make it easy for your JS code to access session
    data like username, email address, or gravatar URL, that you might want to
    show in the user interface.

    The rest of this docstring is slightly adapted from Werkzeug's SecureCookie
    class.

    This module implements a cookie that is not alterable from the client
    because it adds a checksum the server checks for.  You can use it as
    session replacement if all you have is a user id or something to mark
    a logged in user.

    Keep in mind that the data is still readable from the client as a
    normal cookie is.  However you don't have to store and flush the
    sessions you have at the server.

    Example usage:

    >>> from spa.jwtcookie import JWTCookie
    >>> x = JWTCookie({"foo": 42, "baz": (1, 2, 3)}, "deadbeef")

    Dumping into a string so that one can store it in a cookie:

    >>> value = x.serialize()

    Loading from that string again:

    >>> x = JWTCookie.unserialize(value, "deadbeef")
    >>> x["baz"]
    (1, 2, 3)

    If someone modifies the cookie and the checksum is wrong the unserialize
    method will fail silently and return a new empty `JWTCookie` object.

    Keep in mind that the values will be visible in the cookie so do not
    store data in a cookie you don't want the user to see.

    Application Integration
    =======================

    If you are using the werkzeug request objects you could integrate the
    secure cookie into your application like this::

        from werkzeug.utils import cached_property
        from werkzeug.wrappers import BaseRequest
        from spa.jwtcookie import JWTCookie

        # don't use this key but a different one; you could just use
        # os.urandom(20) to get something random
        SECRET_KEY = '\xfa\xdd\xb8z\xae\xe0}4\x8b\xea'

        class Request(BaseRequest):

            @cached_property
            def client_session(self):
                data = self.cookies.get('session_data')
                if not data:
                    return JWTCookie(secret_key=SECRET_KEY)
                return JWTCookie.unserialize(data, SECRET_KEY)

        def application(environ, start_response):
            request = Request(environ, start_response)

            # get a response object here
            response = ...

            if request.client_session.should_save:
                session_data = request.client_session.serialize()
                response.set_cookie('session_data', session_data,
                                    httponly=True)
            return response(environ, start_response)

    A less verbose integration can be achieved by using shorthand methods::

        class Request(BaseRequest):

            @cached_property
            def client_session(self):
                return JWTCookie.load_cookie(self, secret_key=COOKIE_SECRET)

        def application(environ, start_response):
            request = Request(environ, start_response)

            # get a response object here
            response = ...

            request.client_session.save_cookie(response)
            return response(environ, start_response)
"""

from __future__ import print_function

from datetime import timedelta
from six.moves.http_cookies import SimpleCookie
from six.moves.urllib.parse import parse_qs

import jwt
import utc
from werkzeug._compat import text_type
from werkzeug.contrib.sessions import ModificationTrackingDict
from werkzeug.http import dump_cookie


class TokenTimestampError(Exception): pass

class JWTCookie(ModificationTrackingDict):

    """Represents a secure cookie.

    Example usage:

    >>> x = JWTCookie({"foo": 42, "baz": (1, 2, 3)}, "deadbeef")
    >>> x["foo"]
    42
    >>> x["baz"]
    (1, 2, 3)
    >>> x["blafasel"] = 23
    >>> x.should_save
    True

    :param data: the initial data, as a dictionary.
    :param secret_key: the secret key.  If not set `None` or not specified
                       it has to be set before :meth:`serialize` is called.
    :param algorithm: A string indicating the algorithm to be used.  Must be
                      supported by the PyJWT library.
    """

    def __init__(self, data=None, secret_key=None, algorithm='HS256'):
        ModificationTrackingDict.__init__(self, data or ())
        # explicitly convert it into a bytestring because python 2.6
        # no longer performs an implicit string conversion on hmac
        if secret_key is not None and not isinstance(secret_key, bytes):
            secret_key = bytes(secret_key, 'utf8')
        self.secret_key = secret_key
        self.algorithm = algorithm

    def __repr__(self):
        return '<%s %s%s>' % (
            self.__class__.__name__,
            dict.__repr__(self),
            self.should_save and '*' or ''
        )

    @property
    def should_save(self):
        """True if the session should be saved.  By default this is only true
        for :attr:`modified` cookies, not :attr:`new`.
        """
        return self.modified

    def serialize(self, expires=None):
        """Serialize the secure cookie into a string.

        If expires is provided, the session will be automatically invalidated
        after expiration when you unseralize it. This provides better
        protection against session cookie theft.

        :param expires: an optional expiration date for the cookie (a
                        :class:`datetime.datetime` object)
        """
        if self.secret_key is None:
            raise RuntimeError('no secret key defined')
        if expires:
            self['exp'] = expires
        self['iat'] = utc.now()
        return jwt.encode(self, self.secret_key, self.algorithm)

    @classmethod
    def unserialize(cls, string, secret_key, algorithm='HS256', expire_days=None):

        """Load the secure cookie from a serialized string.

        :param string: the cookie value to unserialize.
        :param secret_key: the secret key used to serialize the cookie.
        :return: a new :class:`JWTCookie`.
        """
        if isinstance(string, text_type):
            string = string.encode('utf-8', 'replace')
        if isinstance(secret_key, text_type):
            secret_key = secret_key.encode('utf-8', 'replace')

        items = jwt.decode(string, secret_key, algorithms=[algorithm])

        if expire_days:
            if 'iat' not in items:
                raise TokenTimestampError('No iat claim in token')

            issued_at = utc.fromtimestamp(items['iat'])
            if (utc.now() - issued_at).days > expire_days:
                raise TokenTimestampError('Token is too old')

        return cls(items, secret_key, algorithm)

    @classmethod
    def load_cookie(cls, request, key='session', secret_key=None):
        """Loads a :class:`JWTCookie` from a cookie in request.  If the
        cookie is not set, a new :class:`JWTCookie` instanced is
        returned.

        :param request: a request object that has a `cookies` attribute
                        which is a dict of all cookie values.
        :param key: the name of the cookie.
        :param secret_key: the secret key used to decode the cookie.
                           Always provide the value even though it has
                           no default!
        """
        data = request.cookies.get(key)
        if not data:
            return cls(secret_key=secret_key)
        return cls.unserialize(data, secret_key)

    def save_cookie(self, response, key='session', expires=None,
                    session_expires=None, max_age=None, path='/', domain=None,
                    secure=None, httponly=False, force=False):
        """Saves the JWTCookie in a cookie on response object.  All parameters
        that are not described here are forwarded directly to
        :meth:`~BaseResponse.set_cookie`.

        :param response: a response object that has a
                         :meth:`~BaseResponse.set_cookie` method.
        :param key: the name of the cookie.
        :param session_expires: the expiration date of the secure cookie
                                stored information.  If this is not provided
                                the cookie `expires` date is used instead.
        """
        if force or self.should_save:
            data = self.serialize(session_expires or expires)
            response.set_cookie(key, data, expires=expires, max_age=max_age,
                                path=path, domain=domain, secure=secure,
                                httponly=httponly)


class JWTSessionMiddleware(object):
    def __init__(self, app, secret_key, cookie_name='session',
                 wsgi_name='jwtsession', expire_days=1,
                 algorithm='HS256'):
        self.app = app
        self.secret_key = secret_key
        self.cookie_name = cookie_name
        self.wsgi_name = wsgi_name
        self.expire_days = expire_days
        self.algorithm = algorithm

    def __call__(self, environ, start_response):
        # on the way in: if environ includes our cookie, then deserialize it and
        # stick it back into environ as jwtsession.  If environ doesn't include
        # one then make an empty one and stick that in.
        if 'HTTP_COOKIE' in environ:
            cookie = SimpleCookie(environ['HTTP_COOKIE'])
            if self.cookie_name in cookie:
                try:
                    session = JWTCookie.unserialize(
                        cookie[self.cookie_name].value,
                        self.secret_key,
                        self.algorithm,
                        expire_days=self.expire_days,
                    )
                except (jwt.DecodeError, TokenTimestampError):
                    session = JWTCookie({}, self.secret_key, self.algorithm)
            else:
                session = JWTCookie({}, self.secret_key, self.algorithm)
        else:
            session = JWTCookie({}, self.secret_key, self.algorithm)
        environ[self.wsgi_name] = session


        # on the way out: serialize jwtsession and stick it into headers as
        # 'session'.
        def session_start_response(status, headers, exc_info=None):
            # TODO: make this smarter so we can avoid sending cookies with
            # static file requests.
            if session.should_save or session == {}:
                # add our cookie to headers
                c = dump_cookie(self.cookie_name,
                                value=environ[self.wsgi_name].serialize(),
                                max_age=timedelta(days=self.expire_days))
                headers.append(('Set-Cookie', c))
            return start_response(status, headers, exc_info=exc_info)

        return self.app(environ, session_start_response)


class JWTSessionParamMiddleware(object):
    """
    This middleware supports setting session values from a query string
    parameter (signed as a JSON Web Token).

    This middleware must be used with some other middleware that actually
    provides the session functionality.
    """
    def __init__(self, app, secret_key, expire_days=1, algorithm='HS256',
                 qs_name='session_token', wsgi_name='jwtsession'):
        self.app = app
        self.secret_key = secret_key
        self.expire_days = expire_days
        self.algorithm = algorithm
        self.qs_name = qs_name
        self.wsgi_name = wsgi_name

    def __call__(self, environ, start_response):
        qs_params = {k: v[0] for k, v in
                     parse_qs(environ['QUERY_STRING']).items()}
        if self.qs_name not in qs_params:
            return self.app(environ, start_response)
        try:
            session_vals = jwt.decode(qs_params[self.qs_name], key=self.secret_key)
        except jwt.DecodeError:
            # silently drop malformed tokens
            return self.app(environ, start_response)

        if self.expire_days:
            if 'iat' not in session_vals:
                # We can't enforce token expiration if the token has no issued
                # at claim.  So ignore the token.
                return self.app(environ, start_response)

            issued_at = utc.fromtimestamp(session_vals['iat'])
            if (utc.now() - issued_at).days > self.expire_days:
                # Token has an issued at claim, but it's too old.  Ignore the
                # token.
                return self.app(environ, start_response)

        environ[self.wsgi_name].update(session_vals)
        return self.app(environ, start_response)
