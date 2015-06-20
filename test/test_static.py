import os

from werkzeug.test import Client

import spa
from spa.static import StaticHandler

def test_static_handler():

    here = os.path.dirname(os.path.realpath(__file__))
    static_folder = os.path.join(here, 'static')

    routes = (
        ('/<path:filepath>', 'test', StaticHandler, {'directory': static_folder}),
    )

    app = spa.App(routes)
    c = Client(app, spa.Response)
    resp = c.get('/css/test.css')
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/css'
