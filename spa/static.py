import mimetypes
import os
import sys
import posixpath
from zlib import adler32
from time import time, mktime
from datetime import datetime

from spa.handler import Handler
from werkzeug.exceptions import NotFound
from werkzeug.wrappers import BaseResponse
from werkzeug.wsgi import get_path_info, wrap_file
from werkzeug._compat import iteritems, string_types, PY2
from werkzeug.http import is_resource_modified, http_date


class StaticHandler(Handler):
    def __init__(self, app, req, params, directory, disallow=None, cache=True,
                 cache_timeout=60 * 60 * 12, fallback_mimetype='text/plain'):
        super(StaticHandler, self).__init__(app, req, params)
        self.cache = cache
        self.cache_timeout = cache_timeout

        if isinstance(directory, tuple):
            loader = self.get_package_loader(*directory)
        elif isinstance(directory, string_types):
            if os.path.isfile(directory):
                loader = self.get_file_loader(directory)
            else:
                loader = self.get_directory_loader(directory)
        else:
            raise TypeError('unknown def %r' % directory)

        self.loader = loader
        if disallow is not None:
            from fnmatch import fnmatch
            self.is_allowed = lambda x: not fnmatch(x, disallow)
        self.fallback_mimetype = fallback_mimetype

    def is_allowed(self, filename):
        """Subclasses can override this method to disallow the access to
        certain files.  However by providing `disallow` in the constructor
        this method is overwritten.
        """
        return True

    def _opener(self, filename):
        return lambda: (
            open(filename, 'rb'),
            datetime.utcfromtimestamp(os.path.getmtime(filename)),
            int(os.path.getsize(filename))
        )

    def get_file_loader(self, filename):
        return lambda x: (os.path.basename(filename), self._opener(filename))

    def get_package_loader(self, package, package_path):
        from pkg_resources import DefaultProvider, ResourceManager, \
             get_provider
        loadtime = datetime.utcnow()
        provider = get_provider(package)
        manager = ResourceManager()
        filesystem_bound = isinstance(provider, DefaultProvider)
        def loader(path):
            if path is None:
                return None, None
            path = posixpath.join(package_path, path)
            if not provider.has_resource(path):
                return None, None
            basename = posixpath.basename(path)
            if filesystem_bound:
                return basename, self._opener(
                    provider.get_resource_filename(manager, path))
            return basename, lambda: (
                provider.get_resource_stream(manager, path),
                loadtime,
                0
            )
        return loader

    def get_directory_loader(self, directory):
        def loader(path):
            if path is not None:
                path = os.path.join(directory, path)
            else:
                path = directory
            if os.path.isfile(path):
                return os.path.basename(path), self._opener(path)
            return None, None
        return loader

    def generate_etag(self, mtime, file_size, real_filename):
        if not isinstance(real_filename, bytes):
            real_filename = real_filename.encode(sys.getfilesystemencoding())
        return 'wzsdm-%d-%s-%s' % (
            mktime(mtime.timetuple()),
            file_size,
            adler32(real_filename) & 0xffffffff
        )



    def get_filename_and_loader(self, path):
        file_loader = None
        exports = {'': self.loader}
        for search_path, loader in iteritems(exports):
            if search_path == path:
                real_filename, file_loader = loader(None)
                if file_loader is not None:
                    break
            if not search_path.endswith('/'):
                search_path += '/'
            if path.startswith(search_path):
                real_filename, file_loader = loader(path[len(search_path):])
                if file_loader is not None:
                    break

        return real_filename, file_loader

    def get(self, path):
        #cleaned_path = get_path_info(environ)
        if PY2:
            path = path.encode(sys.getfilesystemencoding())
        # sanitize the path for non unix systems
        path = path.strip('/')
        for sep in os.sep, os.altsep:
            if sep and sep != '/':
                path = path.replace(sep, '/')
        path = '/' + '/'.join(x for x in path.split('/')
                              if x and x != '..')

        real_filename, file_loader = self.get_filename_and_loader(path)
        if file_loader is None or not self.is_allowed(real_filename):
            return NotFound()

        guessed_type = mimetypes.guess_type(real_filename)
        mime_type = guessed_type[0] or self.fallback_mimetype
        f, mtime, file_size = file_loader()


        def resp(environ, start_response):
            headers = [('Date', http_date())]
            if self.cache:
                timeout = self.cache_timeout
                etag = self.generate_etag(mtime, file_size, real_filename)
                headers += [
                    ('Etag', '"%s"' % etag),
                    ('Cache-Control', 'max-age=%d, public' % timeout)
                ]
                if not is_resource_modified(environ, etag, last_modified=mtime):
                    f.close()
                    start_response('304 Not Modified', headers)
                    return []
                headers.append(('Expires', http_date(time() + timeout)))
            else:
                headers.append(('Cache-Control', 'public'))

            headers.extend((
                ('Content-Type', mime_type),
                ('Content-Length', str(file_size)),
                ('Last-Modified', http_date(mtime))
            ))
            start_response('200 OK', headers)
            return wrap_file(environ, f)
        return resp

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
