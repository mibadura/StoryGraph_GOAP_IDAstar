import json
import os

import azure.functions as func

from json_validation.json_schema import schema


def open_file(path):
    func_dir = os.path.dirname(__file__)
    return open(os.path.join(func_dir, path), encoding="utf8")


def main(req: func.HttpRequest) -> func.HttpResponse:
    if req.route_params.get('example_type') == 'schema':
        resp_data = json.dumps(schema, indent=4)
        resp_code = 200
        resp_mimetype = 'application/json'
    else:
        resp_data = ''
        resp_code = 400
        resp_mimetype = 'text/plain'

    return func.HttpResponse(
        resp_data,
        status_code=resp_code,
        mimetype=resp_mimetype
    )
