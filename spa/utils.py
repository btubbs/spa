import os
import sys

from gunicorn.app.base import Application as GunicornApplication
from werkzeug._compat import PY2


def import_class(path):
    try:
        module, dot, klass = path.rpartition('.')
        imported = __import__(module, globals(), locals(), [klass, ], -1)
        return getattr(imported, klass)
    except Exception, e:
        raise ImportError(e)


class SpaGunicornApplication(GunicornApplication):
    """
    Wrapper around gunicorn so we can start app from a console entry point
    instead of a big ugly gunicorn line.
    """

    worker_class = 'gwebsocket.gunicorn.GWebSocketWorker'
    accesslog = '-'
    default_port = 8000

    def __init__(self, wsgi_app, port=None, gunicorn_config=None):
        self.app = wsgi_app
        self.port = port or os.getenv('PORT', self.default_port)
        self.gunicorn_config = gunicorn_config or {}
        super(GunicornApplication, self).__init__()

    def init(self, *args):
        config = dict(self.gunicorn_config)
        config['bind'] = config.get('bind', '0.0.0.0:%s' % self.port)
        config['worker_class'] = config.get('worker_class', self.worker_class)
        return config

    def load(self):
        return self.app


def run(app, port=None, gunicorn_config=None):
    gunicorn_app = SpaGunicornApplication(app, port, gunicorn_config)
    gunicorn_app.run()


def clean_path(path):
    if PY2:
        path = path.encode(sys.getfilesystemencoding())
    # sanitize the path for non unix systems
    path = path.strip('/')
    for sep in os.sep, os.altsep:
        if sep and sep != '/':
            path = path.replace(sep, '/')
    path = '/' + '/'.join(x for x in path.split('/')
                          if x and x != '..')
    return path
