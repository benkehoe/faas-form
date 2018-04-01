"""
Created on Mar 30, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

import six
import getpass
from abc import abstractmethod, ABCMeta
import re
import itertools

from . import getch

__all__ = [
    'Schema',
    'StringInput',
    'SecretInput',
    'NumberInput',
    'StringListInput',
    'ConstInput',
    'BooleanInput',
]

class SchemaError(ValueError):
    pass

class Schema(object):
    INPUT_REGISTRY = {}
    
    @classmethod
    def _input_from_json(cls, obj):
        input_type = obj.get('type')
        if input_type not in cls.INPUT_REGISTRY:
            raise SchemaError("Invalid input type: {}".format(input_type))
        input_cls = cls.INPUT_REGISTRY[input_type]
        return input_cls.from_json(obj)
    
    @classmethod
    def from_json(cls, obj):
        if 'inputs' not in obj:
            raise SchemaError('Missing inputs')
        
        instructions = obj.get('instructions')
        
        inputs = []
        for input_obj in obj['inputs']:
            inputs.append(cls._input_from_json(input_obj))
        
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
        return obj
    
    def get_values(self):
        if self.instructions:
            print(self.instructions)
        values = {}
        for input_obj in self.inputs:
            values[input_obj.name] = input_obj.get_value()
        return values
    
    def __repr__(self):
        instructions_str = ''
        if self.instructions:
            instructions_str = ',instructions={!r}'.format(self.instructions)
        return 'Schema({!r}{})'.format(self.inputs, instructions_str)

@six.add_metaclass(ABCMeta)
class Input(object):
    REQUIRED_DEFAULT = True
    
    @classmethod
    @abstractmethod
    def from_json(cls, obj):
        raise NotImplementedError
    
    @classmethod
    def _get_base_kwargs_from_json(cls, obj):
        if 'name' not in obj:
            raise SchemaError("Name is required")
        kwargs = {
            'name': obj['name'],
        }
        for field in ['required', 'help']:
            if field in obj:
                kwargs[field] = obj[field]
        if cls.default_allowed():
            kwargs['default'] = obj.get('default')
        elif 'default' in obj:
            raise SchemaError("Default is not allowed for type {}".format(cls.type()))
        return kwargs
    
    @classmethod
    @abstractmethod
    def type(cls):
        raise NotImplementedError
    
    @classmethod
    def default_allowed(cls):
        return True
    
    def __init__(self, name,
                 required=None,
                 default=None,
                 help=None,):
        if not name:
            raise SchemaError("Name is required")
        self.name = name
        self._required = required
        self.help = help
        
        self.default = None
        if self.default_allowed():
            self.default = default
        elif default is not None:
            raise SchemaError("Default is not allowed for type {}".format(self.type()))
    
    @property
    def required(self):
        return self._required if self._required is not None else self.REQUIRED_DEFAULT
    
    @required.setter
    def required(self, value):
        self._required = value
    
    def _base_to_json(self, *args):
        obj = {
            'name': self.name,
            'type': self.type(),
        }
        for field in ['required', 'default', 'help'] + list(args):
            value = getattr(self, field)
            if value is not None:
                obj[field] = value
        return obj
    
    @abstractmethod
    def to_json(self):
        raise NotImplementedError
    
    def _input(self, prompt):
        from six.moves import input
        return input(prompt)
    
    @abstractmethod
    def _get_value(self, prompt):
        raise NotImplementedError
    
    def _properties_for_prompt(self):
        properties = []
        if self._required is not None or self.required:
            properties.append('required={}'.format(self.required))
        if self.default_allowed() and self.default is not None:
            properties.append('default={}'.format(self.default))
        return properties
    
    def prompt(self):
        parts = [
            '{} [{}]'.format(self.name, self.type())
        ]
        if self.help:
            parts.append(' {}'.format(self.help))
        properties = self._properties_for_prompt()
        if properties:
            parts.append(' ({})'.format(', '.join(properties)))
        parts.append(': ')
        return ''.join(parts)
    
    def get_value(self):
        prompt = self.prompt()
        while True:
            try:
                value = self._get_value(prompt)
            except EOFError:
                print('')
                value = None
            if value is None and self.default is not None:
                value = self.default
            if value is None and self.required:
                print("Field is required!")
                continue
            break
        return value
    
    def __repr__(self):
        json_value = self.to_json()
        kwargs = [
            'name='+repr(json_value['name']),
        ]
        for key, value in json_value.items():
            if key in ['name', 'type']:
                continue
            kwargs.append('{}={!r}'.format(key, value))
        return '{}({})'.format(self.__class__.__name__, ','.join(kwargs))

class StringInput(Input):
    @classmethod
    def type(cls):
        return 'string'
    
    @classmethod
    def from_json(cls, obj):
        kwargs = cls._get_base_kwargs_from_json(obj)
        kwargs['pattern'] = obj.get('pattern')
        return cls(**kwargs)
    
    def __init__(self, name,
                 required=None,
                 default=None,
                 help=None,
                 pattern=None,):
        super(StringInput, self).__init__(
            name,
            required=required,
            default=default,
            help=help)
        self.pattern = pattern
    
    def to_json(self):
        return self._base_to_json('pattern')
    
    def _get_value(self, prompt):
        while True:
            value = self._input(prompt)
            if self.pattern and not re.search(self.pattern, value):
                print('Invalid input!')
                continue
            if not value:
                value = None
            return value

class SecretInput(StringInput):
    @classmethod
    def type(cls):
        return 'secret'
    
    @classmethod
    def default_allowed(cls):
        return False
    
    def __init__(self, name,
                 required=None,
                 help=None,
                 pattern=None,):
        super(SecretInput, self).__init__(name, required=required, help=help, pattern=pattern)
    
    def _input(self, prompt):
        return getpass.getpass(prompt)

class NumberInput(Input):
    @classmethod
    def type(cls):
        return 'number'
    
    @classmethod
    def from_json(cls, obj):
        kwargs = cls._get_base_kwargs_from_json(obj)
        kwargs['integer'] = obj.get('integer')
        return cls(**kwargs)
    
    def __init__(self, name,
                 required=None,
                 default=None,
                 help=None,
                 integer=None):
        super(NumberInput, self).__init__(
            name,
            required=required,
            default=default,
            help=help)
        
        self.integer = integer
        
    def to_json(self):
        return self._base_to_json('integer')
    
    def _properties_for_prompt(self):
        properties = super(NumberInput, self)._properties_for_prompt()
        if self.integer is True:
            properties.append('integer={}'.format(self.integer))
        return properties
    
    def _get_value(self, prompt):
        while True:
            value = self._input(prompt)
            try:
                value = float(value)
                if self.integer and not value.is_integer():
                    print('Value must be an integer!')
                    continue
                return value
            except ValueError:
                print('Invalid input! Ctrl-D to enter no value')

class StringListInput(Input):
    @classmethod
    def type(cls):
        return 'list<string>'
    
    @classmethod
    def default_allowed(cls):
        return False
    
    @classmethod
    def from_json(cls, obj):
        kwargs = cls._get_base_kwargs_from_json(obj)
        kwargs['pattern'] = obj.get('pattern')
        kwargs['size'] = obj.get('size')
        return cls(**kwargs)
    
    def __init__(self, name,
                 required=None,
                 default=None,
                 help=None,
                 pattern=None,
                 size=None,):
        super(StringListInput, self).__init__(
            name,
            required=required,
            default=default,
            help=help)
        
        self.pattern = pattern
        self.size = size
    
    def to_json(self):
        return self._base_to_json('pattern', 'size')
    
    @property
    def minimum_size(self):
        if self.size is None:
            return 0
        else:
            return self.size
    
    @property
    def maximum_size(self):
        if self.size is None:
            return float('inf')
        else:
            return self.size
    
    def _properties_for_prompt(self):
        properties = super(StringListInput, self)._properties_for_prompt()
        if self.size is not None:
            properties.append('size={}'.format(self.size))
        return properties
    
    def _get_value(self, prompt):
        values = []
        for _ in itertools.count():
            try:
                value = self._input(prompt)
                if self.pattern and not re.search(self.pattern, value):
                    print('Invalid input! Ctrl-D to enter no value')
                    continue
                if not value:
                    value = None
            except EOFError:
                print('')
                value = None
            
            if value is None:
                if len(values) >= self.minimum_size:
                    return values
                else:
                    print("Not enough values! Minimum size: {}".format(self.minimum_size))
                    continue
            
            values.append(value)
            
            if len(values) == self.maximum_size:
                return values

class ConstInput(Input):
    @classmethod
    def type(cls):
        return 'const'
    
    @classmethod
    def default_allowed(cls):
        return False
    
    @classmethod
    def from_json(cls, obj):
        kwargs = cls._get_base_kwargs_from_json(obj)
        kwargs.pop('required', None) # Const is special
        if 'value' not in obj:
            raise SchemaError("value is required")
        kwargs['value'] = obj['value']
        return cls(**kwargs)
    
    def __init__(self, name, value,
                 help=None):
        super(ConstInput, self).__init__(
            name,
            help=help)
        self.value = value
    
    def to_json(self):
        return self._base_to_json('value')
    
    def _get_value(self, prompt):
        return self.value

class BooleanInput(Input):
    @classmethod
    def type(cls):
        return 'boolean'
    
    @classmethod
    def default_allowed(cls):
        return False
    
    @classmethod
    def from_json(cls, obj):
        kwargs = cls._get_base_kwargs_from_json(obj)
        return cls(**kwargs)
    
    def __init__(self, name,
                 required=None,
                 help=None):
        super(BooleanInput, self).__init__(
            name,
            required=required,
            help=help)
    
    def to_json(self):
        return self._base_to_json()
    
    def _get_value(self, prompt):
        while True:
            value = getch.getch(prompt).lower()
            if value not in ['y', 'n']:
                print('Enter y/n')
            else:
                return value == 'y'

for input_cls in [
        StringInput,
        SecretInput,
        NumberInput,
        StringListInput,
        ConstInput,
        BooleanInput,
        ]:
    Schema.INPUT_REGISTRY[input_cls.type()] = input_cls
