"""
Created on Mar 31, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

import six
import json

import boto3
from botocore.exceptions import ClientError

from . import payloads
from .schema import Schema

class RequestError(Exception):
    pass

class FaaSFunction(object):
    MARKER = 'faasform'
    
    @classmethod
    def list(cls, tags=True, env=True, session=None):
        session = session or boto3.session.Session()
        
        funcs = {}
        
        if tags:
            client = session.client('resourcegroupstaggingapi')
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
            client = session.client('lambda')
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
    def _get_arn(cls, name, session=None):
        if name.startswith('arn'):
            return name
        
        session = session or boto3.session.Session()
        client = session.client('lambda')
        response = client.get_function(
            FunctionName=name
        )
        return response['Configuration']['FunctionArn']
    
    @classmethod
    def add(cls, name, description=None, session=None):
        session = session or boto3.session.Session()
        
        arn = cls._get_arn(name, session=session)
        
        client = session.client('resourcegroupstaggingapi')
        
        client.tag_resources(
            ResourceARNList=[arn],
            Tags={
                cls.MARKER: description or ''
            }
        )
    
    @classmethod
    def remove(cls, name, session=None):
        session = session or boto3.session.Session()
        
        arn = cls._get_arn(name, session=session)
        
        client = session.client('resourcegroupstaggingapi')
        
        client.untag_resources(
            ResourceARNList=[arn],
            TagKeys=[cls.MARKER],
        )
    
    def __init__(self, id, name=None, description=None, session=None):
        self.id = id
        self.name = name
        self.description = description
        self.session = session or boto3.session.Session()
        
    def get_schema(self):
        client = self.session.client('lambda')
        
        payload = {}
        payloads.set_schema_request(payload)
        
        response = client.invoke(
            FunctionName=self.id,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload),
        )
        
        response_payload = json.load(response['Payload'])
        
        return Schema.from_json(response_payload)
    
    def invoke(self, values):
        client = self.session.client('lambda')
        
        payload = {}
        payloads.set_invoke_request(payload)
        
        payload.update(values)
        
        response = client.invoke(
            FunctionName=self.id,
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload),
        )
        
        return response