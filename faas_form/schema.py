"""
Created on Mar 30, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

import six
import getpass
from abc import abstractmethod, ABCMeta
import re

from six.moves import input

__all__ = [
    'Schema',
    'StringInput',
    'SecretInput',
    'NumberInput',
]

class MissingSchemaError(Exception):
    pass

class SchemaError(ValueError):
    pass

class Schema(object):
    INPUT_REGISTRY = {}
    
    KEY = 'x-faas-form-schema'
    
    @classmethod
    def from_json(cls, obj):
        if cls.KEY not in obj:
            raise MissingSchemaError
        
        obj = obj[cls.KEY]
        instructions = obj.get('instructions')
        
        inputs = []
        for input_obj in obj.get('inputs', []):
            input_type = input_obj.get('type')
            if input_type not in cls.INPUT_REGISTRY:
                raise SchemaError("Invalid input type: {}".format(input_type))
            input_cls = cls.INPUT_REGISTRY[input_type]
            inputs.append(input_cls.from_json(input_obj))
        
        return cls(inputs, instructions=instructions)
    
    def __init__(self, inputs, instructions=None):
        self.instructions = instructions
        self.inputs = inputs
    
    def to_json(self):
        obj = {
            'inputs': [i.to_json() for i in self.inputs],
        }
        if self.instructions:
            obj['instructions'] = self.instructions
        return {
            self.key: obj,
        }
    
    def prompt(self):
        if self.instructions:
            print(self.instructions)
        values = {}
        for input_obj in self.inputs:
            values[input_obj.name] = input_obj.prompt()
        return values

@six.add_metaclass(ABCMeta)
class Input(object):
    @classmethod
    @abstractmethod
    def from_json(cls, obj):
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def type(cls):
        raise NotImplementedError
    
    def __init__(self, name, help=None):
        if not name:
            raise SchemaError("Name is required")
        self.name = name
        self.help = help
    
    @abstractmethod
    def to_json(self):
        raise NotImplementedError
    
    def prompt_str(self):
        help_str = ' {}'.format(self.help) if self.help else ''
        return '{} [{}]{}: '.format(self.name, self.type(), help_str)
    
    @abstractmethod
    def prompt(self):
        raise NotImplementedError

class StringInput(Input):
    @classmethod
    def from_json(cls, obj):
        return cls(
            obj['name'],
            help=obj.get('help'),
            pattern=obj.get('pattern'),
            default=obj.get('default'),
        )
    
    @classmethod
    def type(cls):
        return 'string'
    
    def __init__(self, name,
                 help=None,
                 pattern=None,
                 default=None):
        super(StringInput, self).__init__(name, help=help)
        
        self.pattern = pattern
        self.default = default
    
    def to_json(self):
        obj = {
            'name': self.name,
        }
        for field in ['help', 'pattern', 'default']:
            value = getattr(self, field)
            if value is not None:
                obj[field] = value
        return obj
    
    def _input(self, prompt):
        return input(prompt)
    
    def prompt(self):
        while True:
            value = self._input(self.prompt_str())
            if not value and self.default is not None:
                return self.default
            if self.pattern and not re.search(self.pattern, value):
                print('Invalid input!')
                continue
            return value

class SecretInput(StringInput):
    @classmethod
    def from_json(cls, obj):
        return cls(
            obj['name'],
            help=obj.get('help'),
            pattern=obj.get('pattern'),
        )
    @classmethod
    def type(cls):
        return 'secret'
    
    def __init__(self, name,
                 help=None,
                 pattern=None):
        super(SecretInput, self).__init__(name, help=help, pattern=pattern, default=None)
    
    def _input(self, prompt):
        return getpass.getpass(prompt)

class NumberInput(Input):
    @classmethod
    def from_json(cls, obj):
        return cls(
            obj['name'],
            help=obj.get('help'),
            default=obj.get('default'),
        )
    
    @classmethod
    def type(cls):
        return 'number'
    
    def __init__(self, name,
                 help=None,
                 default=None):
        super(NumberInput, self).__init__(name, help=help)
        
        self.default = default
    
    def to_json(self):
        obj = {
            'name': self.name,
        }
        for field in ['help', 'default']:
            value = getattr(self, field)
            if value is not None:
                obj[field] = value
        return obj
    
    def prompt(self):
        while True:
            value = input(self.prompt_str())
            if not value and self.default:
                return self.default
            try:
                return float(value)
            except ValueError:
                print('Invalid input!')

for input_cls in [
        StringInput,
        SecretInput,
        NumberInput]:
    Schema.INPUT_REGISTRY[input_cls.type()] = input_cls
