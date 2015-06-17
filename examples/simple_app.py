from gevent.monkey import patch_all; patch_all()

import spa

class Home(spa.Handler):
    def get(self):
        msg = "This is a sample Spa application.  Try visiting /hello/joe/."
        return spa.Response(msg)

class Hello(spa.Handler):
    def get(self, name):
        return spa.Response('Hello %s!' % name)

routes = (
    ('/', 'home', Home),
    ('/hello/<name>/', 'hello', Hello),
)

app = spa.App(routes)
spa.run(app)
