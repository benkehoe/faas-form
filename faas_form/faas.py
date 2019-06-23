"""
Created on Mar 31, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

import six
import json
from abc import ABCMeta, abstractmethod
import collections

import boto3
from botocore.exceptions import ClientError

from . import payloads
from .schema import Schema

class RequestError(Exception):
    pass

FunctionInfo = collections.namedtuple('FunctionInfo', ['id', 'name', 'description'])

InvocationResponse = collections.namedtuple('InvocationResponse', ['status', 'payload', 'response', 'logs'])

@six.with_metaclass(ABCMeta)
class FaaSProvider(object):
    MARKER = 'faasform'
    
    @abstractmethod
    def list(self, tags=True, env=False):
        """:rtype: dict[str, FunctionInfo]"""
        raise NotImplementedError
    
    @abstractmethod
    def tag(self, id, description):
        raise NotImplementedError
    
    @abstractmethod
    def untag(self, id):
        raise NotImplementedError

    @abstractmethod
    def _invoke(self, id, payload, logs=False):
        """:rtype: InvocationResponse"""
        raise NotImplementedError
    
    def get_schema(self, id):
        request_payload = {}
        payloads.set_schema_request(request_payload)
        
        response = self._invoke(id, request_payload)
        
        response_payload = response.payload
        
        schema = payloads.get_schema(response_payload)
        
        return Schema.from_json(schema)
    
    def invoke(self, id, values):
        request_payload = {}
        payloads.set_invoke_request(request_payload)
        
        request_payload.update(values)
        
        response = self._invoke(id, request_payload, logs=True)
        
        return response

class LambdaProvider(FaaSProvider):
    def __init__(self, session=None):
        self.session = session or boto3.session.Session()
    
    def list(self, tags=True, env=False):
        funcs = {}
        
        if tags:
            client = self.session.client('resourcegroupstaggingapi')
            paginator = client.get_paginator('get_resources')
            
            paginator_kwargs = {
                'TagFilters': [
                    {
                        'Key': self.MARKER,
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
                        if tag['Key'] == self.MARKER:
                            description = tag.get('Value')
                            break
                    funcs[name] = FunctionInfo(id=arn, name=name, description=description)
        
        if env:
            client = self.session.client('lambda')
            paginator = client.get_paginator('list_functions')
            
            for response in paginator.paginate():
                for func in response['Functions']:
                    arn = func['FunctionArn']
                    name = arn.split(':', 6)[-1]
                    
                    for var_name, var_value in six.iteritems(func.get('Environment', {}).get('Variables', {})):
                        if var_name == self.MARKER:
                            description = var_value or None
                            funcs[name] = FunctionInfo(id=arn, name=name, description=description)
                            break
        
        return funcs
    
    def _get_arn(self, name):
        if name.startswith('arn'):
            return name

        client = self.session.client('lambda')
        response = client.get_function(
            FunctionName=name
        )
        return response['Configuration']['FunctionArn']
    
    def tag(self, id, description=None):
        arn = self._get_arn(id)
        
        client = self.session.client('resourcegroupstaggingapi')
        
        client.tag_resources(
            ResourceARNList=[arn],
            Tags={
                self.MARKER: description or ''
            }
        )
    
    def untag(self, id):
        arn = self._get_arn(id)
        
        client = self.session.client('resourcegroupstaggingapi')
        
        client.untag_resources(
            ResourceARNList=[arn],
            TagKeys=[self.MARKER],
        )
    
    @abstractmethod
    def _invoke(self, id, payload, logs=False):
        client = self.session.client('lambda')
        
        response = client.invoke(
            FunctionName=id,
            InvocationType='RequestResponse',
            LogType='Tail' if logs else None,
            Payload=json.dumps(payload),
        )
        
        return InvocationResponse(
            status=response['StatusCode'],
            payload=json.load(response['Payload']),
            response=response,
            logs=response.get('LogResult'),
        )
