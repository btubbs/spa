import json

from werkzeug.wrappers import BaseRequest, BaseResponse


class Response(BaseResponse): pass

class Request(BaseRequest): pass

class JSONResponse(Response):
    def __init__(self, data, *args, **kwargs):
        kwargs['content_type'] = 'application/json'
        return super(JSONResponse, self).__init__(json.dumps(data), *args, **kwargs)

