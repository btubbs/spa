from gevent.monkey import patch_all; patch_all()

import time

import spa

class Counter(spa.Handler):
    def websocket(self):
        counter = 0
        while True:
            self.ws.send(str(counter))
            counter += 1
            time.sleep(1)

routes = (
    ('/', 'counter', Counter),
)

app = spa.App(routes)
spa.run(app)
