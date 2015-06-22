import json
import traceback

from werkzeug.exceptions import HTTPException

from werkzeug import exceptions


# Some freestanding methods for feeding into our dynamically-constructed
# exception classes later.  They override the corresponding HTTPException
# methods to produce JSON output.

def init(self, description=None, response=None, traceback=None):
    self.traceback = traceback
    HTTPException.__init__(self, description, response)

def get_body(self, environ=None):
    data = dict(
        code=self.code,
        name=self.name,
        description=self.description,
    )
    if self.traceback:
        tb = traceback.format_list(traceback.extract_tb(self.traceback))
        data['traceback'] = tb
    return json.dumps(data)

def get_headers(self, environ=None):
    return [('Content-Type', 'application/json')]


# Loop over all exception classes from werkzeug and dynamically make JSON
# equivalents.
for obj_name in dir(exceptions):
    obj = getattr(exceptions, obj_name)
    if isinstance(obj, type) and issubclass(obj, exceptions.HTTPException):
        new_cls_name = 'JSON' + obj.__name__
        cls = type(new_cls_name, (obj,), dict(
            get_body=get_body,
            get_headers=get_headers,
            __init__=init,
        ))
        globals()[new_cls_name] = cls
