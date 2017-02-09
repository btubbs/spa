import logging
import re
import string
import random
from six.moves.http_cookies import SimpleCookie

from werkzeug.http import dump_cookie
from werkzeug import exceptions

from spa import gzip_util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


COMPRESSABLE_MIMETYPES = (
    'text/plain',
    'text/html',
    'text/css',
    'application/json',
    'application/javascript',
    'application/x-javascript',
    'text/xml',
    'application/xml',
    'application/xml+rss',
    'text/javascript'
)


class GzipMiddleware(object):
    def __init__(self, app, compress_level=6,
                 compressable_mimetypes=COMPRESSABLE_MIMETYPES):
        self.app = app
        self.compress_level = compress_level
        self.compressable_mimetypes = compressable_mimetypes

    def __call__(self, environ, start_response):
        encode_header = environ.get('HTTP_ACCEPT_ENCODING', '')
        if not gzip_util.gzip_requested(encode_header):
            return self.app(environ, start_response)

        buffer = {'to_gzip': False, 'body': ''}

        def _write(body):
            # for WSGI compliance
            buffer['body'] = body

        def _start_response_wrapper(status, headers, exc_info=None):
            ''' Wrapper around the original `start_response` function.
                The sole purpose being to add the proper headers automatically.
            '''
            for header in headers:
                field = header[0].lower()
                if field == 'content-encoding':
                    # if the content is already encoded, don't compress
                    buffer['to_gzip'] = False
                    break
                elif field == 'content-type':
                    ctype = header[1].split(';')[0]
                    user_agent = environ.get('HTTP_USER_AGENT', '').lower()
                    if ctype in self.compressable_mimetypes and not(
                            'msie' in user_agent
                            and 'javascript' in ctype):
                        buffer['to_gzip'] = True

            buffer['status'] = status
            buffer['headers'] = headers
            buffer['exc_info'] = exc_info
            return _write

        data = self.app(environ, _start_response_wrapper)
        if buffer['status'].startswith('200 ') and buffer['to_gzip']:
            data = gzip_util.compress(data, self.compress_level)
            headers = buffer['headers']
            headers.append(('Content-Encoding', 'gzip'))
            headers.append(('Vary', 'Accept-Encoding'))
            for i, header in enumerate(headers):
                if header[0] == 'Content-Length':
                    # Old content-length header is no longer accurate.
                    # And since we're streaming the gzipped data back bit by bit
                    # instead of gzipping it all at once, we can't actually
                    # compute a new content length.  So we just won't have that
                    # header.
                    headers.pop(i)
                    break

        _writable = start_response(buffer['status'], buffer['headers'],
                                   buffer['exc_info'])

        if buffer['body']:
            _writable(buffer['body'])

        return data


def make_csrf_cookie(name, tok_length):

    tok = ''.join(
        random.choice(string.ascii_letters) for x in range(tok_length)
    )
    return dump_cookie(name, value=tok)


class ApiCSRFMiddleware(object):
    """Middleware that sets a api_csrf cookie on responses, if not already set.
    On POST, PUT, PATCH, and DELETE requests, requires that a X-Api-CSRF header
    be set equal to the cookie value.  If not set, return """

    protected_methods = set(['POST', 'PUT', 'PATCH', 'DELETE'])

    def __init__(self, app, cookie_name='api_csrf', header_name='X-Api-CSRF',
                 tok_length=32, exclude_pattern=None):
        self.app = app
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.tok_length = tok_length
        if exclude_pattern:
            self.exclude_pattern = re.compile(exclude_pattern)
        else:
            self.exclude_pattern = None

    def __call__(self, environ, start_response):
        if self.exclude_pattern and re.match(self.exclude_pattern,
                                             environ['PATH_INFO']):
            return self.app(environ, start_response)
        if environ['REQUEST_METHOD'] in self.protected_methods:
            cookieheader = environ.get('HTTP_COOKIE')
            if not cookieheader:
                logger.info('No cookie header')
                return exceptions.Forbidden()(environ, start_response)

            cookie = SimpleCookie(environ['HTTP_COOKIE']).get(
                self.cookie_name
            )
            if not cookie:
                logger.info('No CSRF cookie')
                return exceptions.Forbidden()(environ, start_response)

            headername = 'HTTP_' + self.header_name.replace('-', '_').upper()
            if headername not in environ:
                logger.info('No CSRF header')
                return exceptions.Forbidden()(environ, start_response)

            if cookie.value != environ[headername]:
                logger.info('Mismatched CSRF cookie and header')
                return exceptions.Forbidden()(environ, start_response)


        def start_response_wrapper(status, headers, exc_info=None):

            if 'HTTP_COOKIE' in environ:
                cookie = SimpleCookie(environ['HTTP_COOKIE'])
                if self.cookie_name not in cookie:
                    headers.append(('Set-Cookie',
                                    make_csrf_cookie(self.cookie_name,
                                                     self.tok_length)))
            else:
                headers.append(('Set-Cookie', make_csrf_cookie(self.cookie_name,
                                                               self.tok_length)))
            return start_response(status, headers, exc_info=exc_info)
        return self.app(environ, start_response_wrapper)
