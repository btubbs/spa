import json

from werkzeug import exceptions


# Some freestanding methods for feeding into our dynamically-constructed
# exception classes later.  They override the corresponding HTTPException
# methods to produce JSON output.
def get_body(self, environ=None):
    return json.dumps(dict(
        code=self.code,
        name=self.name,
        description=self.description,
    ))

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
        ))
        globals()[new_cls_name] = cls
