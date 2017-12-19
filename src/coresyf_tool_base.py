import sys
import os

import shutil

import zipfile

import logging

import json

from cerberus import Validator
from argparse import ArgumentParser

TMP_DIR = os.path.abspath("tmp")

TOOL_DEF_SCHEMA = {
    'name': {
        'type': 'string',
        'required': True,
        'empty': False
    },
    'description': {
        'type': 'string'
    },
    'arguments': {
        'type': 'list',
        'required': True,
        'schema': {
            'type': 'dict',
            'schema': {
                'identifier': {
                    'type': 'string',
                    'required': True,
                    'empty': False
                },
                'name': {
                    'type': 'string',
                    'required': True,
                    'empty': False
                },
                'description': {
                    'type': 'string',
                    'required': True
                },
                'type': {
                    'type': 'string',
                    'allowed': ['data', 'parameter', 'output'],
                    'required': True,
                    'empty': False
                },
                'parameterType': {
                    'type': 'string'
                },
                'dataType': {
                    'type': 'string'
                },
                'default': {
                    'type': 'string',
                    'empty': False
                },
                'options': {
                    'type': 'list',
                    'schema': {
                        'type': 'string'
                    }
                },
                'required': {
                    'type': 'boolean'
                }
            }
        }
    }
}

TOOL_DEF_SCHEMA_VALIDATOR = Validator(TOOL_DEF_SCHEMA)


class InvalidToolDefinitionException(Exception):
    pass

class ToolDefinitionFileNotFound(Exception):
    pass

class CoReSyF_Tool(object):

    def __init__(self, tool_definition_file_name):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.logger.setLevel(logging.DEBUG)
        self.bindings = {}
        self.inputs = []
        self.outputs = []
        self.arg_parser = ArgumentParser()
        try:
            tool_definition_file = open(tool_definition_file_name)
            tool_definition = json.loads(tool_definition_file.read())
            if not TOOL_DEF_SCHEMA_VALIDATOR.validate(tool_definition):
                raise InvalidToolDefinitionException(
                    TOOL_DEF_SCHEMA_VALIDATOR.errors)
            self._parse_arguments_(tool_definition)
        except IOError:
            raise ToolDefinitionFileNotFound(tool_definition_file_name)

    def _from_xsd_type_(self, xsd_type):
        if xsd_type == 'boolean':
            return bool
        else:
            return str

    def _parse_parameter_arg_(self, arg):
        name = '--' + arg['identifier']
        _type = self._from_xsd_type_(arg['parameterType'])
        _help = arg['description']
        kwargs = {}
        if 'options' in arg:
            kwargs['choices'] = arg['options']
        if 'default' in arg:
            kwargs['default'] = arg['default']
        if 'required' in arg:
            kwargs['required'] = arg['required']
        self.arg_parser.add_argument(name, type=_type, help=_help, **kwargs)
        self.logger.debug('Parsed %s parameter argument.', name)

    def _parse_data_arg_(self, arg):
        name = arg['identifier']
        _help = arg['description']
        kwargs = {}
        self.arg_parser.add_argument('--' + name, help=_help, **kwargs)
        self.inputs.append(name)
        self.logger.debug('Parsed %s data argument.', name)

    def _parse_output_arg_(self, arg):
        name = arg['identifier']
        _help = arg['description']
        kwargs = {}
        self.arg_parser.add_argument('--' + name, help=_help, required=True, **kwargs)
        self.outputs.append(name)
        self.logger.debug('Parsed %s output argument.', name)

    def _parse_arguments_(self, tool_definition):
        has_required_input = False
        for arg in tool_definition['arguments']:
            if arg['type'] == 'parameter':
                self._parse_parameter_arg_(arg)
            elif arg['type'] == 'data':
                self._parse_data_arg_(arg)
                if 'required' in arg and arg['required']:
                    has_required_input = True
            elif arg['type'] == 'output':
                self._parse_output_arg_(arg)
        if not self.inputs:
            self.arg_parser.error('Input data argument missing.')
        if not has_required_input:
            self.arg_parser.error('No input data argument is specified as required.')
        if not self.outputs:
            self.arg_parser.error('Output data argument missing.')
        self.arguments = self.arg_parser.parse_args()

    def execute(self):
        self.logger.info('Executing.')
        self.bindings = vars(self.arguments)
        self.logger.debug('Bindings: %s', str(self.bindings))
        self.logger.info('Preparing inputs.')
        self._prepare_inputs_(self.bindings)
        self.logger.info('Running.')
        self.run(self.bindings)
        self.logger.info('Cleaning temporary data.')
        self._clean_tmp_()

    def _unzip_file_(self, file_name):
        extracted_files = None
        self.logger.debug('Trying to unzip %s.', file_name)
        if zipfile.is_zipfile(file_name):
            self.logger.info('Extracting %s .', file_name)
            archive = zipfile.ZipFile(file_name, 'r')
            if not archive.infolist():
                self.arg_parser.error(
                    "Input zip file '{}' is empty.".format(file_name))
            archive.extractall(TMP_DIR)
            archive.close()
            extracted_files = [os.path.join(TMP_DIR, f)
                               for f in os.listdir(TMP_DIR)]
        return extracted_files

    def _prepare_inputs_(self, arguments):
        for argname in self.inputs:
            if argname in arguments and arguments[argname]:
                file_name = arguments[argname]
                if not os.path.exists(file_name):
                    self.arg_parser.error("{} does not exists.".format(file_name))
                else:
                    extracted_files = self._unzip_file_(file_name)
                    if extracted_files:
                        self.bindings[argname] = extracted_files[0]

    def _clean_tmp_(self):
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def run(self, bindings):
        pass
