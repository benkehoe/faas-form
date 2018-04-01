"""
client:
{
  "x-faas-form-request": "schema"
}

response:
{
  "x-faas-form-schema": {
    "instructions": "foo",
    "inputs": [
      {
        "name": "bar",
        "type": "string",
        "pattern": "regex",
        "default": "value",
      }
    ]
  }
}

client:
{
  "x-faas-form-request": "invoke",
  "bar": "quux"
}

"""

from __future__ import absolute_import, print_function

from faas_form.payloads import is_schema_request, is_invoke_request, set_reinvoke_response, set_result
from .schema import *