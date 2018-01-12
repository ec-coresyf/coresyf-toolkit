from datetime import date
import logging

from argparse import ArgumentParser
from coresyf_manifest import validate_manifest, InvalidManifestException, MANIFEST_SCHEMA


class CoReSyFArgumentParser():

    MANIFEST_FILE_NAME = 'manifest.json'

    def __init__(self, manifest, args=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.bindings = {}
        self.inputs = []
        self.outputs = []
        self.options = []
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
            def parse_boolean(value):
                if value == 'true':
                    return True
                elif value == 'false':
                    return False
                elif value == 1:
                    return True
                elif value == 0:
                    return False
                else:
                    raise ValueError('invalid literal for boolean: {}'.format(value))
            return parse_boolean
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
        if arg['parameterType'] == 'boolean':
            self.options.append(arg['identifier'])

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
        for opt in self.options:
            self.bindings[opt] = self.bindings[opt] if opt in self.bindings else False

