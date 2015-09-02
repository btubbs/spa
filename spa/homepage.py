import os
import posixpath

from spa.wrappers import Response
from spa.static.smart import get_hash, add_hash_to_filepath

BASE_TEMPLATE = """<!DOCTYPE HTML>
<html>
<head>
{stylesheets}
{extra_head}
</head>
{body}
{scripts}
{extra_foot}
</html>
"""

class HomePage(object):
    template = BASE_TEMPLATE
    rendered = None

    def __init__(self, static_url, static_handler, hash_paths=True,
                 body='<body></body>', scripts=None, stylesheets=None,
                 extra_head='', extra_foot='', template=None):

        self.static_url = static_url
        self.static_handler = static_handler
        self.hash_paths = hash_paths
        self.body = body
        self.scripts = scripts or []
        self.stylesheets = stylesheets or []
        self.extra_head = extra_head
        self.extra_foot = extra_foot

        if template:
            self.template = template

    def build_url(self, filepath):
        if filepath.startswith('/'):
            filepath = filepath[1:]

        if self.hash_paths:
            abs_path = os.path.join(self.static_handler.directory, filepath)
            with open(abs_path) as f:
                file_hash = get_hash(f)

            filepath = add_hash_to_filepath(filepath, file_hash)
        return posixpath.join(self.static_url, filepath)

    def stylesheet_tag(self, stylesheet):
        tmpl = '<link rel="stylesheet" type="text/css" href="{url}" />'
        return tmpl.format(url=self.build_url(stylesheet))

    def script_tag(self, script):
        tmpl = '<script type="text/javascript" src="{url}"></script>'
        return tmpl.format(url=self.build_url(script))

    def get_stylesheet_tags(self):
        return '\n'.join([self.stylesheet_tag(s) for s in self.stylesheets])

    def get_script_tags(self):
        return '\n'.join([self.script_tag(s) for s in self.scripts])

    def render(self):
        if self.rendered is None:
            self.rendered = self.template.format(
                stylesheets=self.get_stylesheet_tags(),
                extra_head=self.extra_head,
                body=self.body,
                scripts=self.get_script_tags(),
                extra_foot=self.extra_foot,
            )
        return self.rendered

    def __call__(self, app, req, params):
        return Response(self.render(), content_type='text/html')
