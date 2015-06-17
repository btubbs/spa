from gevent.monkey import patch_all; patch_all()

import time
from datetime import datetime

from werkzeug.utils import redirect

import spa


class Redirect(spa.Handler):
    def get(self):
        return redirect('/swagger.json')


class Time(spa.Handler):
    """
    An API resource that returns a simple value on GET, and a stream of values
    over a websocket.  This is the "RESTSocket" pattern.
    """
    def get(self):
        return spa.Response(datetime.now().isoformat())

    def websocket(self):
        while True:
            self.ws.send(datetime.now().isoformat())
            time.sleep(1)


class APISpec(spa.Handler):
    """
    A Swagger specification for the API provided in this example.  Spa does not
    in any way require Swagger, and has no Swagger-aware code, but Swagger is a
    nice convention.
    """
    def get(self):
        return spa.JSONResponse({
            "swagger": "2.0",
            "info": {
                "version": "1.0.0",
                "title": "Spa API Example",
                "contact": {
                    "name": "Brent Tubbs",
                    "url": "https://github.com/btubbs/spa",
                },
                "license": {
                    "name": "BSD 3-Clause License",
                    "url": "http://opensource.org/licenses/BSD-3-Clause",
                },
            },
            "host": "localhost",
            "schemes": ["http"],
            "basePath": "/api",
            "paths": {
                "/time/": {
                    "get": {
                        "description": "Returns the current time.",
                        "produces": ["text/plain"],
                        "responses": {
                            "200": {
                                "description": "The current time",
                                "schema": {
                                    "type": "string",
                                },
                                "examples": {
                                    "text/plain": "2015-06-13T21:59:52.586962"
                                }
                            }
                        }
                    },
                    # Swagger doesn't specify how to describe websocket
                    # resources, but it does let you extend the spec with x-*
                    # fields.
                    "x-websocket": {
                        "description": "Returns the current time, once per second.",
                        "produces": ["text/plain"],
                        "responses": {
                            "websocket": {
                                "description": "The current time",
                                "schema": {
                                    "type": "string",
                                }
                            }
                        }
                    },
                }
            },
        })


routes = (
    ('/', 'home', Redirect),
    ('/api/time/', 'time', Time),
    ('/swagger.json', 'api_spec', APISpec),
)

app = spa.App(routes)
spa.run(app)
