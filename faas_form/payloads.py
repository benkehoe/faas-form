"""
Created on Mar 31, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

PAYLOAD_TYPE_KEY = 'x-faas-form-payload'

SCHEMA_PAYLOAD = 'schema'

INVOKE_PAYLOAD = 'invoke'

REINVOKE_PAYLOAD = 'reinvoke'

RESULT_KEY = 'x-faas-form-result'

def _set_payload_type(payload, type):
    payload[PAYLOAD_TYPE_KEY] = type

def _is_payload_type(obj, type):
    return isinstance(obj, dict) and obj.get(PAYLOAD_TYPE_KEY) == type


def set_schema_request(request):
    _set_payload_type(request, SCHEMA_PAYLOAD)

def is_schema_payload(obj):
    return _is_payload_type(obj, SCHEMA_PAYLOAD)
is_schema_request = is_schema_payload


def set_invoke_request(request):
    _set_payload_type(request, INVOKE_PAYLOAD)

def is_invoke_request(obj):
    return _is_payload_type(obj, INVOKE_PAYLOAD)


def set_reinvoke_response(response, result=None):
    _set_payload_type(response, REINVOKE_PAYLOAD)
    if result is not None:
        set_result(response, result)

def is_reinvoke_response(obj):
    return _is_payload_type(obj, REINVOKE_PAYLOAD)


def set_result(response, result):
    response[RESULT_KEY] = result

def get_result(response):
    return response.get(RESULT_KEY)

def _strip_payload(payload):
    return dict((key, value) for key, value in payload.items() if not key.startswith('x-faas-form'))