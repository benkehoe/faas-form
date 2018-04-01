"""
Created on Mar 31, 2018

@author: bkehoe
"""

from __future__ import absolute_import, print_function

import six

import unittest

from unittest import mock

from faas_form import schema

SCHEMA_JSON = {
    'x-faas-form-schema': {
        'description': 'some description',
        'inputs': [
            
            {
                'name': 'secret_input_1',
                'type': 'secret',
            },
            {
                'name': 'number_input_1',
                'type': 'number',
            },
            {
                'name': 'pattern_input_1',
                'type': 'string',
                'pattern': '^[^A-Z]+$',
                'help': 'no capitals',
            }
        ]
    }
}



DEFAULT_VALUE_STRING = 'default_string_value'

INPUT_INVALID_NO_NAME = {
    'type': 'string',
}

INPUT_INVALID_NO_TYPE = {
    'name': 'invalid_input_no_type',
}

INPUT_INVALID_BAD_TYPE = {
    'name': 'invalid_input_bad_type',
    'type': 'bad_type',
}

INPUT_STRING_1 = {
    'name': 'string_input_1',
    'type': 'string',
}

INPUT_STRING_WITH_PATTERN = {
    'name': 'string_input_with_pattern',
    'type': 'string',
    'pattern': r'^[^A-Z]+$',
}

INPUT_STRING_WITH_DEFAULT = {
    'name': 'string_input_with_default',
    'type': 'string',
    'default': DEFAULT_VALUE_STRING,
}

INPUT_STRING_REQUIRED = {
    'name': 'string_input_required',
    'type': 'string',
    'required': True,
}

INPUT_STRING_NOT_REQUIRED = {
    'name': 'string_input_not_required',
    'type': 'string',
    'required': False,
}

INPUT_STRING_REQUIRED_WITH_DEFAULT = {
    'name': 'string_input_required',
    'type': 'string',
    'required': True,
    'default': DEFAULT_VALUE_STRING,
}

INPUT_SECRET_1 = {
    'name': 'secret_schema_1',
    'type': 'secret',
}

INPUT_SECRET_WITH_DEFAULT = {
    'name': 'secret_schema_with_default',
    'type': 'secret',
    'default': DEFAULT_VALUE_STRING,
}

DEFAULT_VALUE_NUMBER = 2.7

INPUT_NUMBER_1 = {
    'name': 'number_input_1',
    'type': 'number',
}

INPUT_NUMBER_WITH_DEFAULT = {
    'name': 'number_input_with_default',
    'type': 'number',
    'default': DEFAULT_VALUE_NUMBER,
}

class SchemaTest(unittest.TestCase):
    def test_input_from_json(self):
        si = schema.Schema._input_from_json(INPUT_STRING_1)
        self.assertIsInstance(si, schema.StringInput)
        
        si = schema.Schema._input_from_json(INPUT_SECRET_1)
        self.assertIsInstance(si, schema.SecretInput)
        
        si = schema.Schema._input_from_json(INPUT_NUMBER_1)
        self.assertIsInstance(si, schema.NumberInput)
        
        with self.assertRaises(schema.SchemaError):
            schema.Schema._input_from_json(INPUT_INVALID_NO_NAME)
        
        with self.assertRaises(schema.SchemaError):
            schema.Schema._input_from_json(INPUT_INVALID_NO_TYPE)
        
        with self.assertRaises(schema.SchemaError):
            schema.Schema._input_from_json(INPUT_INVALID_BAD_TYPE)

class StringInputTest(unittest.TestCase):
    def test_from_json(self):
        schema.StringInput.from_json(INPUT_STRING_1)
        schema.StringInput.from_json(INPUT_STRING_WITH_PATTERN)
        schema.StringInput.from_json(INPUT_STRING_WITH_DEFAULT)
        schema.StringInput.from_json(INPUT_STRING_REQUIRED)
        schema.StringInput.from_json(INPUT_STRING_NOT_REQUIRED)
        schema.StringInput.from_json(INPUT_STRING_REQUIRED_WITH_DEFAULT)
        
    
    def test_prompt(self):
        input_values = ['FOO', 'foo']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_1)
            value = si.get_value()
        
        self.assertEqual(value, input_values[0])
        self.assertEqual(mock_input.call_count, 1)
    
    def test_prompt_default_required(self):
        input_values = ['', 'foo']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_1)
            value = si.get_value()
        
        self.assertEqual(value, input_values[1])
        self.assertEqual(mock_input.call_count, 2)
    
    def test_prompt_pattern(self):
        input_values = ['FOO', 'foo']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_WITH_PATTERN)
            value = si.get_value()
        
        self.assertEqual(value, input_values[1])
        self.assertEqual(mock_input.call_count, 2)

    def test_prompt_default(self):
        input_values = ['']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_WITH_DEFAULT)
            value = si.get_value()
        
        self.assertEqual(value, DEFAULT_VALUE_STRING)
        self.assertEqual(mock_input.call_count, 1)
        
        input_values = [EOFError()]
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_WITH_DEFAULT)
            value = si.get_value()
        
        self.assertEqual(value, DEFAULT_VALUE_STRING)
        self.assertEqual(mock_input.call_count, 1)
    
    def test_prompt_required(self):
        input_values = ['', 'foo']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_REQUIRED)
            value = si.get_value()
        
        self.assertEqual(value, input_values[1])
        self.assertEqual(mock_input.call_count, 2)
        
        input_values = [EOFError(), 'foo']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_REQUIRED)
            value = si.get_value()
        
        self.assertEqual(value, input_values[1])
        self.assertEqual(mock_input.call_count, 2)
    
    def test_prompt_not_required(self):
        input_values = ['', 'foo']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_NOT_REQUIRED)
            value = si.get_value()
        
        self.assertEqual(value, None)
        self.assertEqual(mock_input.call_count, 1)
    
    def test_prompt_required_with_default(self):
        input_values = ['', 'foo']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_REQUIRED_WITH_DEFAULT)
            value = si.get_value()
        
        self.assertEqual(value, DEFAULT_VALUE_STRING)
        self.assertEqual(mock_input.call_count, 1)
        
        input_values = [EOFError(), 'foo']
        
        with mock.patch.object(schema.StringInput, '_input', side_effect=input_values) as mock_input:
            si = schema.StringInput.from_json(INPUT_STRING_REQUIRED_WITH_DEFAULT)
            value = si.get_value()
        
        self.assertEqual(value, DEFAULT_VALUE_STRING)
        self.assertEqual(mock_input.call_count, 1)

class SecretInputTest(unittest.TestCase):
    def test_from_json(self):
        schema.SecretInput.from_json(INPUT_SECRET_1)
        with self.assertRaises(schema.SchemaError):
            schema.SecretInput.from_json(INPUT_SECRET_WITH_DEFAULT)

class NumberInputTest(unittest.TestCase):
    def test_from_json(self):
        schema.NumberInput.from_json(INPUT_NUMBER_1)
        schema.NumberInput.from_json(INPUT_NUMBER_WITH_DEFAULT)
        
    
    def test_prompt(self):
        input_values = ['1', '2']
        
        with mock.patch.object(schema.NumberInput, '_input', side_effect=input_values) as mock_input:
            si = schema.NumberInput.from_json(INPUT_NUMBER_1)
            value = si.get_value()
        
        self.assertEqual(value, float(input_values[0]))
        self.assertEqual(mock_input.call_count, 1)
        
        input_values = ['x', '2']
        
        with mock.patch.object(schema.NumberInput, '_input', side_effect=input_values) as mock_input:
            si = schema.NumberInput.from_json(INPUT_NUMBER_1)
            value = si.get_value()
        
        self.assertEqual(value, float(input_values[1]))
        self.assertEqual(mock_input.call_count, 2)
    
    def test_prompt_default(self):
        input_values = [EOFError()]
        
        with mock.patch.object(schema.NumberInput, '_input', side_effect=input_values) as mock_input:
            si = schema.NumberInput.from_json(INPUT_NUMBER_WITH_DEFAULT)
            value = si.get_value()
        
        self.assertEqual(value, DEFAULT_VALUE_NUMBER)
        self.assertEqual(mock_input.call_count, 1)