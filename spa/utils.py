import multiprocessing
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

    default_gunicorn_config = dict(
        worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gwebsocket.gunicorn.GWebSocketWorker'),
        accesslog = '-',
        errorlog = '-',
        workers=os.getenv('GUNICORN_WORKER_COUNT', multiprocessing.cpu_count() * 2),
        # Heroku/Velociraptor-friendly PORT handling.
        bind='0.0.0.0:%s' % os.getenv('PORT', 8000),
        graceful_timeout = os.getenv('GUNICORN_WORKER_GRACETIME', 30),
    )

    def __init__(self, wsgi_app, port=None, gunicorn_config=None):
        self.app = wsgi_app
        self.gunicorn_config = dict(self.default_gunicorn_config)

        gunicorn_config = gunicorn_config or {}
        if port is not None and 'bind' not in gunicorn_config:
            gunicorn_config['bind'] = '0.0.0.0:%s' % port
        self.gunicorn_config.update(gunicorn_config)
        super(GunicornApplication, self).__init__()

    def load_config(self):
        for k, v in self.gunicorn_config.items():
            self.cfg.set(k, v)

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
