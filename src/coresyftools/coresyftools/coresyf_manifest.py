from cerberus import Validator

import json



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


class MissingInputArgument(Exception):
    pass


class MissingOutputArgument(Exception):
    pass


class ManifestFileNotFound(Exception):
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

def get_manifest(manifest_file_name):
    try:
        with open(manifest_file_name) as manifest_file:
            return json.loads(manifest_file.read())
    except IOError:
        raise ManifestFileNotFound(manifest_file_name)
    except ValueError:
        raise ManifestSyntaxError()
