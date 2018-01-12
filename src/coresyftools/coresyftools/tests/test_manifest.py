from unittest import TestCase
from ..manifest import MalformedManifestException, validate_manifest, MissingInputArgument , MissingOutputArgument



class TestValidateManifest(TestCase):

    def test_valid(self):
        base_manifest = {
            "name": "name",
            "description": "description",
            "arguments": [{
                "identifier": "input",
                "name": "input",
                "description": "input description",
                "type": "data",
                "required": True
            }, {
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>",
                "type": "output"
            }]
        }
        validate_manifest(base_manifest)

    def test_missing_key(self):
        manifest = {
            "arguments": [{
                "identifier": "input",
                "name": "input",
                "description": "input description",
                "type": "data",
                "required": True
            }, {
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>",
                "type": "output"
            }]
        }
        self.assertRaises(MalformedManifestException,
                          lambda: validate_manifest(manifest))

    def test_invalid_key(self):
        manifest = {
            "name": "name",
            "description_______": "description",
            "arguments": [{
                "identifier": "input",
                "name": "input",
                "description": "input description",
                "type": "data",
                "required": True
            }, {
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>",
                "type": "output"
            }]
        }
        self.assertRaises(MalformedManifestException,
                          lambda: validate_manifest(manifest))

    def test_no_input(self):
        manifest = {
            "name": "name",
            "description": "description",
            "arguments": [{
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>",
                "type": "output"
            }]
        }
        self.assertRaises(MissingInputArgument,
                          lambda: validate_manifest(manifest))

    def test_no_output(self):
        manifest = {
            "name": "name",
            "description": "description",
            "arguments": [{
                "identifier": "input",
                "name": "input",
                "description": "Sets the output file name to <filepath>",
                "type": "data"
            }]
        }
        self.assertRaises(MissingOutputArgument,
                          lambda: validate_manifest(manifest))
