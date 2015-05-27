import os

from gunicorn.app.base import Application as GunicornApplication


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

    def __init__(self, wsgi_app, gunicorn_config=None):
        self.app = wsgi_app
        self.gunicorn_config = gunicorn_config or {}
        super(GunicornApplication, self).__init__()

    def init(self, *args):
        config = dict(self.gunicorn_config)
        config['bind'] = config.get('bind',
                                    '0.0.0.0:%s' % os.getenv('PORT', 8000))
        config['worker_class'] = config.get('worker_class', self.worker_class)
        return config

    def load(self):
        return self.app


def run_gunicorn(app, gunicorn_config=None):
    gunicorn_app = SpaGunicornApplication(app, gunicorn_config)
    gunicorn_app.run()
