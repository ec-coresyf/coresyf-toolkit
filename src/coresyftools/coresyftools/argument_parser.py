from datetime import date
import logging

from argparse import ArgumentParser
from manifest import validate_manifest, InvalidManifestException, MANIFEST_SCHEMA


class CoReSyFArgumentParser():

    def __init__(self, manifest, logger=None):
        self.identifiers = set()
        self.manifest = manifest
        self.logger = logger or logging.getLogger(__name__)
        self.bindings = {}
        self.inputs = []
        self.outputs = []
        self.options = []
        self.arg_parser = ArgumentParser()
        validate_manifest(self.manifest)
        self._configure_arg_parser()

    def _get_manifest_schema(self):
        return MANIFEST_SCHEMA

    def parse_arguments(self, args=None):
        self.arguments = self.arg_parser.parse_args(args)
        self.bindings = vars(self.arguments)

        self.bindings = dict([(k, v) for k, v in self.bindings.items()
                               if v is not None])
        for opt in self.options:
            self.bindings[opt] = self.bindings[opt] if opt in self.bindings else False

    def _configure_arg_parser(self):
        tool_definition = self.manifest
        if 'parameters' in tool_definition:
            for arg in tool_definition['parameters']:
                self._parse_parameter_arg(arg)
        for arg in tool_definition['inputs']:
            self._parse_data_arg(arg)
        for arg in tool_definition['outputs']:
                self._parse_output_arg(arg)

    def _parse_parameter_arg(self, arg):
        name = arg['identifier']
        _type = self._from_xsd_type_(arg['type'])
        _help = arg['description']
        add_arguments_kwargs = {}
        if 'options' in arg:
            add_arguments_kwargs['choices'] = arg['options']
        if 'default' in arg:
            add_arguments_kwargs['default'] = arg['default']
        if 'required' in arg:
            add_arguments_kwargs['required'] = arg['required']
        self.arg_parser.add_argument('--' + name, type=_type, help=_help,
                                     **add_arguments_kwargs)
        self.logger.debug('Parsed %s parameter argument.', name)
        # The boolean options need to be mantained.
        # ArgumentParser do not define them if they are not passed in the shell.
        # However Wings always need a value for every parameter.
        # If a booelan argument is not passed in the shell it should end up
        # defined as False.
        if arg['type'] == 'boolean':
            self.options.append(name)
        self.identifiers.add(name)

    def _parse_data_arg(self, arg):
        name = arg['identifier']
        _help = arg['description']
        kwargs = {}
        if 'collection' in arg and arg['collection']:
            kwargs['nargs'] = '+'
        self.arg_parser.add_argument('--' + name, help=_help, required=True,
                                     **kwargs)
        self.inputs.append(name)
        self.logger.debug('Parsed %s data argument.', name)
        self.identifiers.add(name)


    def _parse_output_arg(self, arg):
        name = arg['identifier']
        _help = arg['description']
        kwargs = {}
        if 'collection' in arg and arg['collection']:
            kwargs['nargs'] = '+'
        self.arg_parser.add_argument(
            '--' + name, help=_help, required=True, **kwargs)
        self.outputs.append(name)
        self.logger.debug('Parsed %s output argument.', name)
        self.identifiers.add(name)


    @staticmethod
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

    def _from_xsd_type_(self, xsd_type):
        if xsd_type == 'boolean':
            return self.parse_boolean
        elif xsd_type == 'int':
            return int
        elif xsd_type == 'float':
            return float
        elif xsd_type == 'date':
            return date
        elif xsd_type == 'string':
            return str
