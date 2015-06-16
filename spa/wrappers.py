import json

from werkzeug.wrappers import Response, Request as WRequest


class JSONResponse(Response):
    def __init__(self, data, *args, **kwargs):
        kwargs['content_type'] = 'application/json'
        return super(JSONResponse, self).__init__(json.dumps(data), *args, **kwargs)


class Request(WRequest):
    """
    Request with an extra .json() method.
    """
    # This is copied from
    # http://werkzeug.pocoo.org/docs/0.10/request_data/#how-to-extend-parsing,
    # but adapted to have a method instead of an attribute, so parse errors
    # don't get masked and show up as AttributeError.

    # accept up to 4MB of transmitted data.
    max_content_length = 1024 * 1024 * 4

    def json(self):
        if self.headers.get('content-type') == 'application/json':
            return json.loads(self.data)
