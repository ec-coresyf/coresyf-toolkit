import sys
import os

import shutil

import zipfile

import logging

import json

from datetime import date

from cerberus import Validator
from argparse import ArgumentParser

TMP_DIR = os.path.abspath("tmp")

MANIFEST_SCHEMA = {
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
                    'type': 'string',
                    'allowed': ['string', 'boolean', 'int', 'float', 'date']
                },
                'dataType': {
                    'type': 'string'
                },
                'default': {},
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


class ManifestSyntaxError(Exception):
    pass


class MalformedManifestException(Exception):
    pass


class InvalidManifestException(Exception):
    pass


class ManifestFileNotFound(Exception):
    pass


class MissingInputArgument(Exception):
    pass


class MissingOutputArgument(Exception):
    pass


def validate_manifest(manifest):
    manifest_validator = Validator(MANIFEST_SCHEMA)
    if not manifest_validator.validate(manifest):
        raise MalformedManifestException(
            manifest_validator.errors)
    has_input = False
    has_output = False
    for arg in manifest['arguments']:
        if arg['type'] == 'data':
            has_input = True
        if arg['type'] == 'output':
            has_output = True
    if not has_input:
        raise MissingInputArgument()
    if not has_output:
        raise MissingOutputArgument()


class CoReSyFArgParser():

    MANIFEST_FILE_NAME = 'manifest.json'

    def __init__(self, manifest, args=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.bindings = {}
        self.inputs = []
        self.outputs = []
        self.arg_parser = ArgumentParser()
        self.manifest = manifest
        validate_manifest(self.manifest)
        is_valid, errors = self._validate_manifest(self.manifest)
        if not is_valid:
            raise InvalidManifestException(errors)

    def _get_manifest_schema(self):
        return MANIFEST_SCHEMA

    def _validate_manifest(self, manifest):
        return (True, [])

    def _from_xsd_type_(self, xsd_type):
        if xsd_type == 'boolean':
            return bool
        elif xsd_type == 'int':
            return int
        elif xsd_type == 'float':
            return float
        elif xsd_type == 'date':
            return date
        elif xsd_type == 'string':
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
        self.arg_parser.add_argument('--' + name, help=_help, required=True,
                                     **kwargs)
        self.inputs.append(name)
        self.logger.debug('Parsed %s data argument.', name)

    def _parse_output_arg_(self, arg):
        name = arg['identifier']
        _help = arg['description']
        kwargs = {}
        self.arg_parser.add_argument(
            '--' + name, help=_help, required=True, **kwargs)
        self.outputs.append(name)
        self.logger.debug('Parsed %s output argument.', name)

    def _config_arg_parser(self):
        tool_definition = self.manifest
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
      
    def parse_arguments(self, args=None):
        self._config_arg_parser()
        self.arguments = self.arg_parser.parse_args(args)
        self.bindings = vars(self.arguments)
        self.bindings = dict([(k, v) for k, v in self.bindings.items() if v])


def get_manifest(manifest_file_name):
    try:
        with open(manifest_file_name) as manifest_file:
            return json.loads(manifest_file.read())
    except IOError:
        raise ManifestFileNotFound(manifest_file_name)
    except ValueError:
        raise ManifestSyntaxError()


class CoReSyFTool(object):

    def __init__(self, run_script_file_name):
        self.context_directory = self._get_context_directory(run_script_file_name)
        self.manifest_file_name = os.path.join(self.context_directory, self.MANIFEST_FILE_NAME)
        self.manifest = get_manifest(self.manifest_file_name)
        self.arg_parser = CoReSyFArgParser(self.manifest)
        self.arg_parser.parse_arguments()
        self.bindings = self.arg_parser.bindings
        self.logger = logging.getLogger(CoReSyFTool.__name__)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.logger.setLevel(logging.DEBUG)

   

    def _get_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.INFO)
        return logger

    def _get_context_directory(self, run_script_file_name):
        return os.path.dirname(
            os.path.abspath(run_script_file_name))

    def execute(self):
        self.logger.info('Executing.')
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
                self.arg_parser.arg_parser.error(
                    "Input zip file '{}' is empty.".format(file_name))
            archive.extractall(TMP_DIR)
            archive.close()
            extracted_files = [os.path.join(TMP_DIR, f)
                               for f in os.listdir(TMP_DIR)]
        return extracted_files

    def _prepare_inputs_(self, arguments):
        for argname in self.arg_parser.inputs:
            if argname in arguments and arguments[argname]:
                file_name = arguments[argname]
                if not os.path.exists(file_name):
                    self.arg_parser.arg_parser.error(
                        "{} does not exists.".format(file_name))
                else:
                    extracted_files = self._unzip_file_(file_name)
                    if extracted_files:
                        self.bindings[argname] = extracted_files[0]

    def _clean_tmp_(self):
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def run(self, bindings):
        pass
