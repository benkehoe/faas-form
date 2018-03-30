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
from .schema import MissingSchemaError

def main(args=None):
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers()
    
    list_parser = subparsers.add_parser('list', aliases=['ls'])
    list_parser.add_argument('--tags', action='store_true', default=None)
    list_parser.add_argument('--env', action='store_true', default=None)
    list_parser.set_defaults(func=list_funcs)
    
    invoke_parser = subparsers.add_parser('invoke')
    invoke_parser.add_argument('name')
    invoke_parser.set_defaults(func=invoke)
    
    admin_parser = subparsers.add_parser('admin')
    admin_parser.add_argument('command', choices=['add', 'remove', 'rm'])
    admin_parser.add_argument('name')
    admin_parser.add_argument('--description')
    admin_parser.set_defaults(func=admin)
    
    args = parser.parse_args(args=args)
    
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
    except MissingSchemaError as e:
        err_msg = 'ERROR: No schema returned by the function'
        sys.exit(err_msg)
    
    values = schema.prompt()
    
    try:
        response = func.invoke(values)
        
        payload = json.load(response['Payload'])
        
        print('Response:')
        print(json.dumps(payload, indent=2))
    except Exception as e:
        err_msg = 'ERROR: {}'.format(e)
        sys.exit(err_msg)

def admin(parser, args):
    if args.command in ['add']:
        faas.FaaSFunction.add(args.name, args.description)
    elif args.command in ['remove', 'rm']:
        faas.FaaSFunction.remove(args.name)
    else:    
        parser.exit("Unknown command {}".format(args.command))

if __name__ == '__main__':
    main()