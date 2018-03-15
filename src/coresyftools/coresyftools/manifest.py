from cerberus import Validator

import json


MANIFEST_SCHEMA = {
    'name': {
        'type': 'string',
        'required': True,
        'empty': False
    },
    'type': {
        'type': 'string',
        'required': True,
        'empty': False
    },
    'description': {
        'type': 'string'
    },
    'inputs': {
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
                    'type': 'string'
                },
                'collection': {
                    'type': 'boolean'
                }
            }
        }
    },
    'parameters': {
        'type': 'list',
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
                    'allowed': ['string', 'boolean', 'int', 'float', 'date']
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
    },
    'outputs': {
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
                    'type': 'string'
                },
                'collection': {
                    'type': 'boolean'
                }
            }
        }
    },
    'command': {'type': 'string'},
    'operation': {
        'type': 'dict',
        'required': False
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


def get_manifest(manifest_file_name):
    try:
        with open(manifest_file_name) as manifest_file:
            return json.loads(manifest_file.read())
    except IOError:
        raise ManifestFileNotFound(manifest_file_name)
    except ValueError:
        raise ManifestSyntaxError()
