from unittest import TestCase

from coresyf_tool_base import CoReSyFArgParser


class TestCoReSyFArgParser(TestCase):

    def setUp(self):
        self.base_manifest = {
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

    def parse_with_arg(self, arg_def, args):
        manifest = self.base_manifest.copy()
        manifest['arguments'].append(arg_def)
        arg_parser = CoReSyFArgParser(manifest)
        arg_parser.parse_arguments(args)
        return arg_parser

    def test_basic_parse_args(self):
        arg = {
            "identifier": "strparam",
            "name": "string parameter",
            "type": "parameter",
            "parameterType": "string",
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
            "type": "parameter",
            "parameterType": "string",
            "description": "string parameter description",
        }
        command = '--input f1 --output f2 --strparam str'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['strparam'], 'str')

    def test_parse_true_bool_param(self):
        arg = {
            "identifier": "boolparam",
            "name": "boolean parameter",
            "type": "parameter",
            "parameterType": "boolean",
            "description": "boolean parameter description"
        }
        command = '--input f1 --output f2 --boolparam true'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['boolparam'], True)

    def test_parse_false_bool_param(self):
        arg = {
            "identifier": "boolparam",
            "name": "boolean parameter",
            "type": "parameter",
            "parameterType": "boolean",
            "description": "boolean parameter description"
        }
        command = '--input f1 --output f2 --boolparam 0'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['boolparam'], False)

    def test_parse_int_param(self):
        arg = {
            "identifier": "intparam",
            "name": "int parameter",
            "description": "int parameter description",
            "type": "parameter",
            "parameterType": "int"
        }
        command = '--input f1 --output f2 --intparam 3'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['intparam'], 3)

    def test_parse_float_param(self):
        arg = {
            "identifier": "floatparam",
            "name": "float parameter",
            "description": "float parameter description",
            "type": "parameter",
            "parameterType": "float"
        }
        command = '--input f1 --output f2 --floatparam 0.5'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['floatparam'], 0.5)

    def test_parse_default_param(self):
        arg = {
            "identifier": "defaultparam",
            "name": "default parameter",
            "description": "default parameter description",
            "type": "parameter",
            "parameterType": "int",
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
            "type": "parameter",
            "parameterType": "int",
            "options": ["1", "2", "3"]
        }
        command = '--input f1 --output f2 --optparam "2"'
        arg_parser = self.parse_with_arg(arg, command.split())
        self.assertEqual(arg_parser.bindings['optparam'], "2")
