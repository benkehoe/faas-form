"""
Created on Mar 31, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

class MissingSchemaError(Exception):
    pass

PAYLOAD_TYPE_KEY = 'x-faas-form-payload'
SCHEMA_PAYLOAD_TYPE = 'schema'
INVOKE_PAYLOAD_TYPE = 'invoke'
REINVOKE_PAYLOAD_TYPE = 'reinvoke'

SCHEMA_KEY = 'x-faas-form-schema'

RESULT_KEY = 'x-faas-form-result'

def _set_payload_type(payload, type):
    payload[PAYLOAD_TYPE_KEY] = type

def _is_payload_type(obj, type):
    return isinstance(obj, dict) and obj.get(PAYLOAD_TYPE_KEY) == type


def _schema_to_json(schema):
    if isinstance(schema, dict):
        return schema
    else:
        return schema.to_json()

def _set_schema(payload, schema):
    payload[SCHEMA_KEY] = _schema_to_json(schema)

def set_schema_request(request):
    _set_payload_type(request, SCHEMA_PAYLOAD_TYPE)

def is_schema_request(request):
    return _is_payload_type(request, SCHEMA_PAYLOAD_TYPE)

def set_schema_reponse(response, schema):
    _set_schema(response, schema)

def get_schema(response):
    if SCHEMA_KEY not in response:
        raise MissingSchemaError
    return response[SCHEMA_KEY]


def set_invoke_request(request):
    _set_payload_type(request, INVOKE_PAYLOAD_TYPE)

def is_invoke_request(obj):
    return _is_payload_type(obj, INVOKE_PAYLOAD_TYPE)


def set_reinvoke_response(response, schema, result=None):
    _set_payload_type(response, REINVOKE_PAYLOAD_TYPE)
    _set_schema(response, schema)
    if result is not None:
        set_result(response, result)

def is_reinvoke_response(obj):
    return _is_payload_type(obj, REINVOKE_PAYLOAD_TYPE)


def set_result(response, result):
    response[RESULT_KEY] = result

def get_result(response):
    return response.get(RESULT_KEY)

def _strip_payload(payload):
    return dict((key, value) for key, value in payload.items() if not key.startswith('x-faas-form'))