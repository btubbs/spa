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

# Things to test?
# Other http methods.
# sending data via POST/PUT
# JSONResponse
# URL parameters
# kwargs in 4th argument of a route.
