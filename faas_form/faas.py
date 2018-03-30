"""
Created on Mar 31, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

import six
import json

import boto3
from botocore.exceptions import ClientError

from .requests import REQUEST_KEY, SCHEMA_REQUEST, INVOKE_REQUEST
from .schema import Schema

class RequestError(Exception):
    pass

class FaaSFunction(object):
    MARKER = 'faasform'
    
    @classmethod
    def list(cls, tags=True, env=True):
        funcs = {}
        
        if tags:
            client = boto3.client('resourcegroupstaggingapi')
            paginator = client.get_paginator('get_resources')
            
            paginator_kwargs = {
                'TagFilters': [
                    {
                        'Key': cls.MARKER,
                    },
                ],
                'ResourceTypeFilters': [
                    'lambda:function',
                ]
            }
            
            for response in paginator.paginate(**paginator_kwargs):
                for value in response['ResourceTagMappingList']:
                    arn = value['ResourceARN']
                    name = arn.split(':', 6)[-1]
                    for tag in value['Tags']:
                        if tag['Key'] == cls.MARKER:
                            description = tag.get('Value')
                            break
                    funcs[name] = cls(arn, name=name, description=description)
        
        if env:
            client = boto3.client('lambda')
            paginator = client.get_paginator('list_functions')
            
            for response in paginator.paginate():
                for func in response['Functions']:
                    arn = func['FunctionArn']
                    name = arn.split(':', 6)[-1]
                    
                    for var_name, var_value in six.iteritems(func.get('Environment', {}).get('Variables', {})):
                        if var_name == cls.MARKER:
                            description = var_value or None
                            funcs[name] = cls(arn, name=name, description=description)
                            break
        
        return funcs
    
    @classmethod
    def _get_arn(cls, name):
        if name.startswith('arn'):
            return name
        
        client = boto3.client('lambda')
        response = client.get_function(
            FunctionName=name
        )
        return response['Configuration']['FunctionArn']
    
    @classmethod
    def add(cls, name, description=None):
        arn = cls._get_arn(name)
        
        client = boto3.client('resourcegroupstaggingapi')
        
        client.tag_resources(
            ResourceARNList=[arn],
            Tags={
                cls.MARKER: description or ''
            }
        )
    
    @classmethod
    def remove(cls, name):
        arn = cls._get_arn(name)
        
        client = boto3.client('resourcegroupstaggingapi')
        
        client.untag_resources(
            ResourceARNList=[arn],
            TagKeys=[cls.MARKER],
        )
    
    def __init__(self, id, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description
    
    def get_schema(self):
        client = boto3.client('lambda')
        
        payload = {
            REQUEST_KEY: SCHEMA_REQUEST,
        }
        
        response = client.invoke(
            FunctionName=self.id,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload),
        )
        
        response_payload = json.load(response['Payload'])
        
        return Schema.from_json(response_payload)
    
    def invoke(self, values):
        client = boto3.client('lambda')
        
        payload = {
            REQUEST_KEY: INVOKE_REQUEST,
        }
        
        payload.update(values)
        
        response = client.invoke(
            FunctionName=self.id,
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload),
        )
        
        return response