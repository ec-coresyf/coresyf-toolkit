from unittest import TestCase
from ..manifest import MalformedManifestException, validate_manifest, MissingInputArgument , MissingOutputArgument


class TestValidateManifest(TestCase):

    def test_valid(self):
        base_manifest = {
            "name": "name",
            "type": "Dummy",
            "description": "description",
            "inputs": [{
                "identifier": "input",
                "name": "input",
                "description": "input description"
            }],
            "outputs": [{
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>"
            }]
        }
        validate_manifest(base_manifest)

    def test_missing_key(self):
        manifest = {
            "inputs": [{
                "identifier": "input",
                "name": "input",
                "description": "input description"
            }],
            "outputs": [{
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>"
            }]
        }
        self.assertRaises(MalformedManifestException,
                          lambda: validate_manifest(manifest))

    def test_invalid_key(self):
        manifest = {
            "name": "name",
            "type": "Dummy",
            "description_______": "description",
            "inputs": [{
                "identifier": "input",
                "name": "input",
                "description": "input description"
            }],
            "outputs": [{
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>"
            }]
        }
        self.assertRaises(MalformedManifestException,
                          lambda: validate_manifest(manifest))

    def test_no_input(self):
        manifest = {
            "name": "name",
            "type": "Dummy",
            "description": "description",
            "outputs": [{
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>"
            }]
        }
        self.assertRaises(MalformedManifestException,
                          lambda: validate_manifest(manifest))

    def test_no_output(self):
        manifest = {
            "name": "name",
            "type": "Dummy",
            "description": "description",
            "inputs": [{
                "identifier": "input",
                "name": "input",
                "description": "Sets the output file name to <filepath>"
            }]
        }
        self.assertRaises(MalformedManifestException,
                          lambda: validate_manifest(manifest))
