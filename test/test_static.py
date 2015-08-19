import os

from werkzeug.test import Client

import spa
from spa.static import StaticHandler
from spa.static.smart import SmartStatic, get_hash


here = os.path.dirname(os.path.realpath(__file__))
static_folder = os.path.join(here, 'static')

def test_static_handler():
    routes = (
        ('/<path:filepath>', 'test', StaticHandler, {'directory': static_folder}),
    )

    app = spa.App(routes)
    c = Client(app, spa.Response)
    resp = c.get('/css/test.css')
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/css'


def test_smart_static_handler():
    routes = (
        ('/<path:filepath>', 'test', SmartStatic(directory=static_folder)),
    )

    css_path = os.path.join(static_folder, 'css', 'test.css')
    with open(css_path) as f:
        css_hash = get_hash(f)

    app = spa.App(routes)
    c = Client(app, spa.Response)
    resp = c.get('/css/test.%s.css' % css_hash)
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/css'


def test_smart_static_css():
    """
    Contents of CSS files served by SmartStatic should have url(), @import and
    other internal links updated to include hashes.
    """
    routes = (
        ('/<path:filepath>', 'test', SmartStatic(directory=static_folder)),
    )

    css_path = os.path.join(static_folder, 'css', 'test.css')
    with open(css_path) as f:
        css_hash = get_hash(f)

    app = spa.App(routes)
    c = Client(app, spa.Response)
    resp = c.get('/css/test.%s.css' % css_hash)
    assert resp.status_code == 200

    # css-relative url
    assert 'url("blah.c9a8f43433e4.css")' in resp.data

    # absolute path url
    assert 'url("/css/blah2.54197c389773.css")' in resp.data

    # url with IE compatibility hack
    assert 'url("/font/lato-regular-webfont.97add36de4b3.eot?#iefix")' in resp.data

    # url with fragment but no query string
    assert 'url("/font/lato-regular-webfont.01ee9ec2a839.svg#svgFontName")' in resp.data

    # css-relative url with query string
    assert 'url("../img/background.fb32250cea28.png?foo=bar")' in resp.data
