from unittest import TestCase
from ..argument_parser import CoReSyFArgumentParser


class TestCoReSyFArgParser(TestCase):

    def setUp(self):
        self.base_manifest = {
            "name": "name",
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

    def parse_with_arg(self, arg_def=None, args=[]):
        manifest = self.base_manifest.copy()
        if arg_def:
            manifest['parameters'] = [arg_def]
        arg_parser = CoReSyFArgumentParser(manifest)
        arg_parser.parse_arguments(args)
        print(arg_parser.arg_parser.__class__.__module__)

        return arg_parser

    def test_parse_without_intput(self):
        command = '--output f2'
        self.assertRaises(SystemExit,
                          lambda: self.parse_with_arg(None, command.split()))

    def test_parse_without_output(self):
        command = '--input f1'
        self.assertRaises(SystemExit,
                          lambda: self.parse_with_arg(None, command.split()))

    def test_basic_parse_args(self):
        arg = {
            "identifier": "strparam",
            "name": "string parameter",
            "type": "string",
            "description": "string parameter description",
        }
        command = '--input f1 --output f2'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['input'], 'f1')
        self.assertEqual(arg_parser.bindings['output'], 'f2')

    def test_parse_str_param(self):
        arg = {
            "identifier": "strparam",
            "name": "string parameter",
            "type": "string",
            "description": "string parameter description",
        }
        command = '--input f1 --output f2 --strparam str'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['strparam'], 'str')

    def test_parse_true_bool_param(self):
        arg = {
            "identifier": "boolparam",
            "name": "boolean parameter",
            "type": "boolean",
            "description": "boolean parameter description"
        }
        command = '--input f1 --output f2 --boolparam true'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['boolparam'], True)

    def test_parse_false_bool_param(self):
        arg = {
            "identifier": "boolparam",
            "name": "boolean parameter",
            "type": "boolean",
            "description": "boolean parameter description"
        }
        command = '--input f1 --output f2 --boolparam false'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['boolparam'], False)
    
    def test_parse_invalid_bool_param(self):
        arg = {
            "identifier": "boolparam",
            "name": "boolean parameter",
            "type": "boolean",
            "description": "boolean parameter description"
        }
        command = '--input f1 --output f2 --boolparam invalid_value'
        self.assertRaises(SystemExit, lambda: self.parse_with_arg(arg, command.split()))

    def test_parse_int_param(self):
        arg = {
            "identifier": "intparam",
            "name": "int parameter",
            "description": "int parameter description",
            "type": "int"
        }
        command = '--input f1 --output f2 --intparam 3'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['intparam'], 3)

    def test_parse_float_param(self):
        arg = {
            "identifier": "floatparam",
            "name": "float parameter",
            "description": "float parameter description",
            "type": "float"
        }
        command = '--input f1 --output f2 --floatparam 0.5'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['floatparam'], 0.5)

    def test_parse_default_param(self):
        arg = {
            "identifier": "defaultparam",
            "name": "default parameter",
            "description": "default parameter description",
            "type": "int",
            "default": "1"
        }
        command = '--input f1 --output f2'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['defaultparam'], 1)

    def test_parse_opt_param(self):
        arg = {
            "identifier": "optparam",
            "name": "options parameter",
            "description": "options parameter description",
            "type": "string",
            "options": ["1", "2", "3"]
        }
        command = '--input f1 --output f2 --optparam 2'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['optparam'], "2")

    def test_parse_req_param(self):
        arg = {
            "identifier": "reqparam",
            "name": "required parameter",
            "description": "required parameter description",
            "type": "int",
            "required": True
        }
        command = '--input f1 --output f2 --reqparam 1'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['reqparam'], 1)

    def test_parse_without_req_param(self):
        arg = {
            "identifier": "reqparam",
            "name": "required parameter",
            "description": "required parameter description",
            "type": "int",
            "required": True
        }
        command = '--input f1 --output f2'

        def parse():
            self.parse_with_arg(arg, command.split())
        self.assertRaises(SystemExit, parse)

    def test_collection_input(self):
        manifest = self.base_manifest.copy()
        manifest['inputs'].append({
            'identifier': 'colinput',
            'name': 'collection input',
            'description': 'collection input description',
            'collection': True
        })
        command = '--input f1 --colinput fc1 fc2 fc3 --output f2'
        arg_parser = CoReSyFArgumentParser(manifest)
        arg_parser.parse_arguments(command.split())
        self.assertEqual(arg_parser.bindings['colinput'], ['fc1', 'fc2', 'fc3'])
    
    def test_collection_output(self):
        manifest = self.base_manifest.copy()
        manifest['outputs'].append({
            'identifier': 'coloutput',
            'name': 'collection output',
            'description': 'collection output description',
            'collection': True
        })
        command = '--input f1 --output f2 --coloutput fc2 fc3 fc4'
        arg_parser = CoReSyFArgumentParser(manifest)
        arg_parser.parse_arguments(command.split())
        self.assertEqual(arg_parser.bindings['coloutput'],
                         ['fc2', 'fc3', 'fc4'])
