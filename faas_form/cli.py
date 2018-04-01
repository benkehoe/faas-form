"""
Created on Mar 31, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

import six

import argparse
import json
import sys

from . import faas
from .schema import Schema
from . import payloads

def main(args=None):
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers()
    
    kwargs = {'aliases':['list']} if six.PY3 else {}
    kwargs['help'] = 'Find faas-form compatible functions'
    list_parser = subparsers.add_parser('ls', **kwargs)
    list_parser.add_argument('--tags', action='store_true', default=None, help='Search tags')
    list_parser.add_argument('--env', action='store_true', default=None, help='Search env vars')
    list_parser.set_defaults(func=list_funcs)
    
    invoke_parser = subparsers.add_parser('invoke', help='Call a faas-form compatible function')
    invoke_parser.add_argument('name', help='The function to invoke')
    invoke_parser.set_defaults(func=invoke)
    
    prompt_parser = subparsers.add_parser('prompt', help='Generate an event from a schema')
    prompt_parser.add_argument('schema')
    prompt_parser.add_argument('--output-file', '-o', type=argparse.FileType('w'))
    prompt_parser.set_defaults(func=prompt)
    
    admin_parser = subparsers.add_parser('admin', help='Tag functions as faas-form compatible')
    admin_parser.add_argument('command', choices=['add', 'remove', 'rm'])
    admin_parser.add_argument('name')
    admin_parser.add_argument('--description')
    admin_parser.set_defaults(func=admin)
    
    args = parser.parse_args(args=args)
    
    if not hasattr(args, 'func'):
        parser.print_usage()
        parser.exit(1)
    
    return args.func(parser, args)

def list_funcs(parser, args):
    tags = args.tags
    env = args.env
    if tags is None and env is None:
        tags = True
        env = True
    
    funcs = faas.FaaSFunction.list(tags=tags, env=env)
    
    name_width = 0
    for func_name in six.iterkeys(funcs):
        name_width = max(name_width, len(func_name))
    
    fmt = '{:' + str(name_width) + '}\t{}'
    for func_name, func in six.iteritems(funcs):
        print(fmt.format(func_name, func.description or ''))

def invoke(parser, args):
    func = faas.FaaSFunction(args.name)
    
    try:
        schema = func.get_schema() # :type schema: faas_form.schema.Schema
    except payloads.MissingSchemaError as e:
        err_msg = 'ERROR: No schema returned by the function'
        sys.exit(err_msg)
    
    while True:
        try:
            values = schema.get_values()
        except KeyboardInterrupt:
            print('')
            sys.exit(1)
        
        try:
            response = func.invoke(values)
            
            payload = json.load(response['Payload'])
            
            result = payloads.get_result(payload)
            if result is not None:
                print('Result:')
                print(result)
            else:
                payload_to_print = json.dumps(payloads._strip_payload(payload), indent=2)
                print('Response:')
                print(payload_to_print)
            
            if not payloads.is_reinvoke_response(payload):
                break
            
            schema = Schema.from_json(payloads.get_schema(payload))
        except Exception as e:
            raise #TODO: only print stack trace if verbose requested in args
            err_msg = 'ERROR: {}'.format(e)
            sys.exit(err_msg)

def prompt(parser, args):
    schema = json.loads(args.schema)
    
    if payloads.SCHEMA_KEY in schema:
        schema  = schema[payloads.SCHEMA_KEY]
    schema = Schema.from_json(schema)
    
    try:
        values = schema.get_values()
    except KeyboardInterrupt:
        print('')
        sys.exit(1)
    
    if args.output_file:
        json.dump(values, args.output_file, indent=2)
    else:
        print(json.dumps(values, indent=2))

def admin(parser, args):
    if args.command in ['add']:
        faas.FaaSFunction.add(args.name, args.description)
    elif args.command in ['remove', 'rm']:
        faas.FaaSFunction.remove(args.name)
    else:    
        parser.exit("Unknown command {}".format(args.command))

if __name__ == '__main__':
    main()