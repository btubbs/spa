import hashlib
import mimetypes
import os
import posixpath
import re
from time import time
from six.moves.urllib.parse import urlsplit, urlunsplit

from werkzeug.exceptions import NotFound
from werkzeug.http import is_resource_modified, http_date

from spa.static.handlers import StaticHandler
from spa.utils import clean_path


class HashCache(object):
    def __init__(self):
        self.path_hashes = {}
        self.contents = {}

    def get_path_hash(self, path):
        return self.path_hashes.get(path)

    def set_path_hash(self, path, path_hash):
        self.path_hashes[path] = path_hash

    def get_contents(self, path):
        return self.contents.get(path)

    def set_contents(self, path, contents):
        self.contents[path] = contents


class CacheBustingStaticHandler(StaticHandler):

    css_url_patterns = (
        (re.compile(r"""(url\(['"]{0,1}\s*(.*?)["']{0,1}\))""", re.IGNORECASE),
         """url("{hashed_url}")"""),
        (re.compile(r"""(@import\s*["']\s*(.*?)["'])""", re.IGNORECASE),
         """@import url("{hashed_url}")"""),
    )

    def __init__(self, app, req, params, route_name, directory, hash_cache,
                 hash_paths=True, static_url_root='/static/', **kwargs):
        self.hash_cache = hash_cache
        self.hash_paths = hash_paths
        self.static_url_root = static_url_root
        return super(CacheBustingStaticHandler, self).__init__(
            app, req, params, route_name, directory, **kwargs
        )


    def get_path_hash(self, unhashed_path):
        if self.hash_cache.get_path_hash(unhashed_path) is None:
            # compute hash, and cache it.
            file = self.get_file(unhashed_path)
            if file is None:
                return None
            try:
                hash_str = get_hash(file.handle)
                self.hash_cache.set_path_hash(unhashed_path, hash_str)
            finally:
                file.handle.close()
        return self.hash_cache.get_path_hash(unhashed_path)


    def get(self, filepath):
        if not self.hash_paths:
            return super(CacheBustingStaticHandler, self).get(filepath)

        unhashed_path, path_hash = parse_hashed_filepath(filepath)
        if unhashed_path is None:
            return NotFound()


        # If hash we were passed doesn't equal the one we've computed and
        # cached, then 404.
        computed_hash = self.get_path_hash(unhashed_path)
        if computed_hash is None:
            return NotFound()
        if path_hash != computed_hash:
            return NotFound()

        # For CSS stylesheets only, we'll rewrite content so that url()
        # functions will point to hashed filenames instead of unhashed.  The
        # rewritten CSS content will be kept in memory.
        if mimetypes.guess_type(filepath)[0] == 'text/css':
            return self.make_css_response(unhashed_path)
        return super(CacheBustingStaticHandler, self).get(unhashed_path)

    def make_css_response(self, filepath):

        def resp(environ, start_response):
            file = self.get_file(filepath)
            try:
                headers = [('Date', http_date())]
                if self.cache:
                    timeout = self.cache_timeout
                    etag = self.generate_etag(file.mtime, file.size, file.name)
                    headers += [
                        ('Etag', '"%s"' % etag),
                        ('Cache-Control', 'max-age=%d, public' % timeout)
                    ]
                    if not is_resource_modified(environ, etag, last_modified=file.mtime):
                        start_response('304 Not Modified', headers)
                        return []
                    headers.append(('Expires', http_date(time() + timeout)))
                else:
                    headers.append(('Cache-Control', 'public'))

                contents = self.hash_cache.get_contents(filepath)

                if contents is None:
                    contents = file.handle.read().decode('utf-8')
                    for pat, tpl in self.css_url_patterns:
                        converter = self.get_converter(tpl)
                        contents = pat.sub(converter, contents)
                    self.hash_cache.set_contents(filepath, contents)

                headers.extend((
                    ('Content-Type', file.mimetype),
                    ('Content-Length', len(contents)),
                    ('Last-Modified', http_date(file.mtime))
                ))
                start_response('200 OK', headers)

                return [contents.encode('utf-8')]
            finally:
                file.handle.close()
        return resp

    def get_converter(self, tpl):
        def converter(matchobj):
            matched, url = matchobj.groups()
            if url.startswith(('#', 'http:', 'https:', 'data:', '//')):
                # These kinds of URLs should be left untouched.
                return matched
            return tpl.format(hashed_url=self.convert_css_url(url))
        return converter

    def convert_css_url(self, css_url):
        split_url = urlsplit(css_url)
        url_path = split_url.path
        if not url_path.startswith('/'):
            abs_url_path = self.make_path_absolute(url_path)
        else:
            abs_url_path = posixpath.realpath(url_path)

        prefix = self.get_url_prefix()

        # now make the path as it would be passed in to this handler when
        # requested from the web.  From there we can use existing methods on the
        # class to resolve to a real file.
        _, _, content_filepath = abs_url_path.partition(prefix)
        content_filepath = clean_path(content_filepath)

        content_file_hash = self.hash_cache.get_path_hash(content_filepath)
        if content_file_hash is None:
            content_file = self.get_file(content_filepath)
            if content_file is None:
                return 'NOT FOUND: "%s"' % url_path
            try:
                content_file_hash = get_hash(content_file.handle)
            finally:
                content_file.handle.close()
        parts = list(split_url)
        parts[2] = add_hash_to_filepath(url_path, content_file_hash)

        url = urlunsplit(parts)

        # Special casing for a @font-face hack, like url(myfont.eot?#iefix")
        # http://www.fontspring.com/blog/the-new-bulletproof-font-face-syntax
        if '?#' in css_url:
            parts = list(urlsplit(url))
            if not parts[3]:
                parts[2] += '?'
            url = urlunsplit(parts)
        return url

    def get_url_prefix(self):
        """
        Return the mount point for this handler.  So if you had a route like
        this:

        ('/foo/bar/static/<path:filepath>', 'foo', Handler)

        Then this function should return '/foo/bar/static/'
        """
        env = self.request.environ
        filepath = self.params['filepath']
        prefix, _, _ = (env['SCRIPT_NAME'] +
                        env['PATH_INFO']).rpartition(filepath)
        return prefix

    def make_path_absolute(self, path):
        """
        Given a relative url found inside the CSS file we're currently serving,
        return an absolute form of that URL.
        """
        env = self.request.environ
        pinfo = posixpath.dirname(env['PATH_INFO'])
        return posixpath.realpath(env['SCRIPT_NAME'] + pinfo + '/' + path)


def parse_hashed_filepath(filename, hash_len=12):
    """
    Given a name like '/static/my_file.deadbeef1234.txt', return a tuple of the file name
    without the hash, and the hash itself, like this:

        ('/static/my_file.txt', 'deadbeef1234')

    If no hash part is found, then return (None, None).
    """
    pat = '^(?P<before>.*)\.(?P<hash>[0-9,a-f]{%s})(?P<after>.*?)$' % hash_len
    m = re.match(pat, filename)
    if m is None:
        return None, None
    parts = m.groupdict()
    return '{before}{after}'.format(**parts), parts['hash']


def add_hash_to_filepath(filepath, hash_str):
    path, filename = os.path.split(filepath)
    root, ext = os.path.splitext(filename)
    return os.path.join(path, "%s.%s%s" % (root, hash_str, ext))


def get_hash(f, hash_len=12):
    # Read the file in 1KB chunks and feed them into the md5 object as you
    # go so you don't burn memory on big files.  Note that this will run forever
    # if you feed it a never-ending file-like object.
    md5 = hashlib.md5()
    while True:
        chunk = f.read(1024)
        if chunk == b'':
            break
        md5.update(chunk)
    return md5.hexdigest()[:hash_len]


class SmartStatic(object):
    """
    A factory for making CacheBustingStaticHandler instances that share a cache
    instance.
    """

    def __init__(self, directory, hash_paths=True):
        self.directory = directory
        self.hash_paths = hash_paths
        self.hash_cache = HashCache()

    def __call__(self, app, req, params, route_name, **kwargs):
        return CacheBustingStaticHandler(app, req, params, route_name,
                                         directory=self.directory,
                                         hash_paths=self.hash_paths,
                                         hash_cache=self.hash_cache,
                                         **kwargs)
