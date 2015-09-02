from werkzeug.test import Client

import spa

def test_get():
    class Hello(spa.Handler):
        def get(self):
            return spa.Response('hello')

    routes = (
        ('/', 'hello', Hello),
    )

    app = spa.App(routes)
    c = Client(app, spa.Response)
    resp = c.get('/')
    assert resp.status_code == 200
    assert resp.data == 'hello'


def test_post():
    class Echo(spa.Handler):
        def post(self):
            return spa.Response(self.request.data)
    app = spa.App((
        ('/', 'echo', Echo),
    ))
    c = Client(app, spa.Response)
    resp = c.post('/', data='some data')
    assert resp.data == 'some data'


def test_put():
    class Echo(spa.Handler):
        def put(self):
            return spa.Response(self.request.data)
    app = spa.App((
        ('/', 'echo', Echo),
    ))
    c = Client(app, spa.Response)
    resp = c.put('/', data='some data')
    assert resp.data == 'some data'


def test_route_kwargs():
    class Kwargy(spa.Handler):
        def __init__(self, app, req, params, some_kwarg, **kwargs):
            self.some_kwarg = some_kwarg
            super(Kwargy, self).__init__(app, req, params, **kwargs)

        def get(self):
            return spa.Response(self.some_kwarg)

    app = spa.App((
        ('/', 'kwargy', Kwargy, {'some_kwarg': 'foo'}),
    ))
    c = Client(app, spa.Response)
    resp = c.get('/')
    assert resp.data == 'foo'


def test_json_response():
    class A(spa.Handler):
        def get(self):
            return spa.JSONResponse({'a': 1})

    app = spa.App((
        ('/', 'a', A),
    ))
    c = Client(app, spa.Response)
    resp = c.get('/')
    assert resp.data == '{"a": 1}'
    assert resp.headers['Content-Type'] == "application/json"


def test_path_args():
    class A(spa.Handler):
        def get(self, country, city):
            return spa.Response("%s: %s" % (country, city))

    app = spa.App((
        ('/country/<country>/city/<city>/', 'a', A),
    ))
    c = Client(app, spa.Response)
    resp = c.get('/country/Poland/city/Warsaw/')
    assert resp.data == 'Poland: Warsaw'


def test_reverse_url():
    class A(spa.Handler):
        def get(self, foo, bar):
            return spa.JSONResponse({'a': 1})

    app = spa.App((
        ('/a/<foo>/b/<bar>/', 'a', A),
    ))

    assert app.url('a', foo=1, bar=2) == '/a/1/b/2/'


def test_json_handler():
    class A(spa.JSONHandler):
        def get(self):
            return {'a': 1}
    app = spa.App((
        ('/', 'a', A),
    ))
    c = Client(app, spa.Response)
    resp = c.get('/')
    assert resp.data == '{"a": 1}'
    assert resp.headers['Content-Type'] == "application/json"
