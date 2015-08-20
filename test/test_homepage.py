import os

from werkzeug.test import Client

import spa
from spa.static.smart import SmartStatic
from spa.homepage import HomePage



here = os.path.dirname(os.path.realpath(__file__))
static_url = '/static/'
static_folder = os.path.join(here, 'static')

def test_homepage_scripts():
    static_handler = SmartStatic(directory=static_folder)

    home_page = HomePage(static_url, static_handler,
        scripts=['js/test1.js', 'js/test2.js'],
    )
    routes = (
        ('/', 'home', home_page),
        (static_url + '<path:filepath>', 'static', static_handler),
    )
    app = spa.App(routes)
    c = Client(app, spa.Response)
    resp = c.get('/')

    expected_tags = [
        '<script type="text/javascript" src="/static/js/test1.5475b9391ae5.js"></script>',
        '<script type="text/javascript" src="/static/js/test2.de48a5238f6c.js"></script>',
    ]

    for t in expected_tags:
        assert t in resp.data

def test_homepage_stylesheet():
    static_handler = SmartStatic(directory=static_folder)

    home_page = HomePage(static_url, static_handler,
        stylesheets=['css/test.css'],
    )
    routes = (
        ('/', 'home', home_page),
        (static_url + '<path:filepath>', 'static', static_handler),
    )
    app = spa.App(routes)
    c = Client(app, spa.Response)
    resp = c.get('/')

    expected_tags = [
        '<link rel="stylesheet" type="text/css" href="/static/css/test.9ed67fcada19.css" />'
    ]

    for t in expected_tags:
        assert t in resp.data
        '<script type="text/javascript" src="/static/js/test1.5475b9391ae5.js"></script>',
        '<script type="text/javascript" src="/static/js/test2.de48a5238f6c.js"></script>',

def test_homepage_extra():
    static_handler = SmartStatic(directory=static_folder)

    home_page = HomePage(static_url, static_handler,
        extra_head='<!-- extra header stuff -->',
        extra_foot='<!-- extra footer stuff -->',
    )
    routes = (
        ('/', 'home', home_page),
        (static_url + '<path:filepath>', 'static', static_handler),
    )
    app = spa.App(routes)
    c = Client(app, spa.Response)
    resp = c.get('/')
    assert '<!-- extra header stuff -->' in resp.data
    assert '<!-- extra footer stuff -->' in resp.data
