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
    
    tags_group = list_parser.add_mutually_exclusive_group()
    tags_group.add_argument('--tags', action='store_true', default=None, help='Search tags')
    tags_group.add_argument('--no-tags', action='store_false', dest='tags', help='Do not search tags')
    
    env_group = list_parser.add_mutually_exclusive_group()
    env_group.add_argument('--env', action='store_true', default=None, help='Search env vars')
    env_group.add_argument('--no-env', action='store_false', dest='env', help='Do not search env vars')
    
    list_parser.set_defaults(func=run_list_funcs)
    
    invoke_parser = subparsers.add_parser('invoke', help='Call a faas-form compatible function')
    invoke_parser.add_argument('name', help='The function to invoke')
    invoke_parser.add_argument('--no-reinvoke', action='store_true', default=False, help='Disable reinvoke functionality')
    invoke_parser.add_argument('--schema', type=json.loads, help='Use the given schema instead of querying the function')
    invoke_parser.set_defaults(func=run_invoke)
    
    prompt_parser = subparsers.add_parser('prompt', help='Generate an event from a schema')
    input_group = prompt_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--schema', type=json.loads)
    input_group.add_argument('--function')
    prompt_parser.add_argument('--output-file', '-o', type=argparse.FileType('w'))
    prompt_parser.set_defaults(func=run_prompt)
    
    admin_parser = subparsers.add_parser('admin', help='Tag functions as faas-form compatible')
    admin_subparsers = admin_parser.add_subparsers()
    
    add_parser = admin_subparsers.add_parser('add', help='Tag a function as faas-form compatible')
    add_parser.add_argument('name')
    add_parser.add_argument('--description')
    add_parser.set_defaults(func=run_admin_add)
    
    rm_parser = admin_subparsers.add_parser('rm', help='Untag a function as faas-form compatible')
    rm_parser.add_argument('name')
    rm_parser.set_defaults(func=run_admin_rm)
    
    show_parser = admin_subparsers.add_parser('show', help='Print the schema for a function')
    show_parser.add_argument('name')
    show_parser.set_defaults(func=run_admin_show)
    
    args = parser.parse_args(args=args)
    
    if not hasattr(args, 'func'):
        parser.print_usage()
        parser.exit(1)
    
    return args.func(parser, args)

def run_list_funcs(parser, args):
    tags = args.tags
    env = args.env
    return list_funcs(tags=tags, env=env)

def list_funcs(tags=None, env=None):
    if tags is None:
        tags = True
    if env is None:
        env = False
    
    funcs = faas.FaaSFunction.list(tags=tags, env=env)
    
    name_width = 0
    for func_name in six.iterkeys(funcs):
        name_width = max(name_width, len(func_name))
    
    fmt = '{:' + str(name_width) + '}\t{}'
    for func_name, func in six.iteritems(funcs):
        print(fmt.format(func_name, func.description or ''))

def run_invoke(parser, args):
    schema = None
    if args.schema is not None:
        schema = Schema.from_json(args.schema)
    
    return invoke(name=args.name, schema=schema, disable_reinvoke=args.no_reinvoke)

def invoke(name, schema=None, disable_reinvoke=False):
    func = faas.FaaSFunction(name)
    
    if not schema:
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
            
            if disable_reinvoke or not payloads.is_reinvoke_response(payload):
                break
            print('')
            
            schema = Schema.from_json(payloads.get_schema(payload))
        except Exception as e:
            raise #TODO: only print stack trace if verbose requested in args
            err_msg = 'ERROR: {}'.format(e)
            sys.exit(err_msg)

def run_prompt(parser, args):
    schema = None
    if args.schema is not None:
        schema = args.schema
        if payloads.SCHEMA_KEY in schema:
            schema  = schema[payloads.SCHEMA_KEY]
        schema = Schema.from_json(schema)
    
    function = None
    if args.function:
        function = faas.FaaSFunction(args.function)
    
    return prompt(schema=schema,
                  function=function,
                  output_file=args.output_file)

def prompt(schema=None, function=None, output_file=None):
    if schema and function:
        raise ValueError("Can't specify both schema and function")
    if not schema and not function:
        raise ValueError("Must specify either schema or function")
    
    if function:
        try:
            schema = function.get_schema() # :type schema: faas_form.schema.Schema
        except payloads.MissingSchemaError as e:
            err_msg = 'ERROR: No schema returned by the function'
            sys.exit(err_msg)
    
    try:
        values = schema.get_values()
    except KeyboardInterrupt:
        print('')
        sys.exit(1)
    
    if output_file:
        json.dump(values, output_file, indent=2)
    else:
        print(json.dumps(values, indent=2))

def run_admin_add(parser, args):
    return admin_add(args.name, description=args.description)

def admin_add(name, description=None):
    return faas.FaaSFunction.add(name, description)

def run_admin_rm(parser, args):
    return admin_rm(args.name)

def admin_rm(name):
    faas.FaaSFunction.remove(name)

def run_admin_show(parser, args):
    return admin_show(args.name)

def admin_show(name):
    function = faas.FaaSFunction(name)
    schema = function.get_schema()
    
    print(json.dumps(schema.to_json(), indent=2))

if __name__ == '__main__':
    main()