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

    def __init__(self, app, **kwargs):
        self.app = app
        self.settings = kwargs
        super(GunicornApplication, self).__init__()

    def init(self, *args):
        default_bind = '0.0.0.0:%s' % os.getenv('PORT', 8000)
        self.settings['bind'] = self.settings.get('bind', default_bind)
        return self.settings

    def load(self):
        return self.app


def run_gunicorn(app, **kwargs):
    SpaGunicornApplication(app, **kwargs).run()
