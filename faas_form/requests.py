"""
Created on Mar 31, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

import six

REQUEST_KEY = 'x-faas-form-request'

SCHEMA_REQUEST = 'schema'

INVOKE_REQUEST = 'invoke'

def _is_request_type(obj, type):
    return isinstance(obj, dict) and obj.get(REQUEST_KEY) == type

def is_schema_request(obj):
    return _is_request_type(obj, SCHEMA_REQUEST)

def is_invoke_request(obj):
    return _is_request_type(obj, INVOKE_REQUEST)
