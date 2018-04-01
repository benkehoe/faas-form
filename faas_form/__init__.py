from __future__ import absolute_import, print_function

def _get_version():
    import pkg_resources, codecs
    if not pkg_resources.resource_exists(__name__, '_version'):
        return '0.0.0'
    return codecs.decode(pkg_resources.resource_string(__name__, '_version'),'utf-8').strip()
__version__ = _get_version()

from faas_form.payloads import (is_schema_request,
                                set_schema_reponse,
                                is_invoke_request,
                                set_result,
                                set_reinvoke_response)
from .schema import *