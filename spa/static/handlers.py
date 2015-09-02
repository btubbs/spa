import mimetypes
import os
import sys
from zlib import adler32
from time import time, mktime
from datetime import datetime
from collections import namedtuple
from pkg_resources import resource_filename

from spa.handler import Handler
from werkzeug.exceptions import NotFound
from werkzeug.wsgi import wrap_file
from werkzeug._compat import iteritems, string_types
from werkzeug.http import is_resource_modified, http_date

from spa.utils import clean_path


File = namedtuple('File', ('handle', 'name', 'mtime', 'size', 'mimetype'))


class StaticHandler(Handler):
    def __init__(self, app, req, params, directory, disallow=None, cache=True,
                 cache_timeout=60 * 60 * 12, fallback_mimetype='text/plain'):
        super(StaticHandler, self).__init__(app, req, params)
        self.cache = cache
        self.cache_timeout = cache_timeout

        if isinstance(directory, tuple):
            directory = resource_filename(*directory)

        if not isinstance(directory, string_types):
            raise TypeError('unknown def %r' % directory)
        loader = self.get_directory_loader(directory)
        self.loader = loader

        self.directory = os.path.realpath(directory)

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

    def get_file(self, path):
        path = clean_path(path)

        real_filename, file_loader = self.get_filename_and_loader(path)
        if file_loader is None or not self.is_allowed(real_filename):
            return None

        guessed_type = mimetypes.guess_type(real_filename)
        mimetype = guessed_type[0] or self.fallback_mimetype
        f, mtime, file_size = file_loader()
        return File(f, real_filename, mtime, file_size, mimetype)

    def make_response(self, file):
        def resp(environ, start_response):
            headers = [('Date', http_date())]
            if self.cache:
                timeout = self.cache_timeout
                etag = self.generate_etag(file.mtime, file.size, file.name)
                headers += [
                    ('Etag', '"%s"' % etag),
                    ('Cache-Control', 'max-age=%d, public' % timeout)
                ]
                if not is_resource_modified(environ, etag, last_modified=file.mtime):
                    file.handle.close()
                    start_response('304 Not Modified', headers)
                    return []
                headers.append(('Expires', http_date(time() + timeout)))
            else:
                headers.append(('Cache-Control', 'public'))

            headers.extend((
                ('Content-Type', file.mimetype),
                ('Content-Length', str(file.size)),
                ('Last-Modified', http_date(file.mtime))
            ))
            start_response('200 OK', headers)
            return wrap_file(environ, file.handle)
        return resp

    def get(self, filepath):
        file = self.get_file(filepath)
        if file is None:
            return NotFound()

        return self.make_response(file)

    def __call__(self, environ, start_response):
        if self.request.method not in self.allowed_methods:
            raise NotImplemented()

        handler = getattr(self, self.request.method.lower())
        resp = handler(**self.params)
        return resp(environ, start_response)


class Static(object):
    """
    A factory for making StaticHandler instances that share a directory
    instance.
    """

    def __init__(self, directory, **kwargs):
        self.directory = directory
        self.kwargs = kwargs

    def __call__(self, app, req, params, **kwargs):
        new_kwargs = dict(self.kwargs)
        new_kwargs.update(kwargs)
        return StaticHandler(app, req, params, directory=self.directory,
                             **new_kwargs)
