from unittest import TestCase

from coresyf_tool_base import CoReSyFArgParser


class TestCoReSyFArgParser(TestCase):

    def setUp(self):
        self.manifest = {
            "name": "name",
            "description": "description",
            "arguments": [{
                "identifier": "input",
                "name": "input",
                "description": "input description",
                "type": "data",
                "required": True
            }, {
                "identifier": "strparam",
                "name": "string parameter",
                "type": "parameter",
                "parameterType": "string",
                "description": "string parameter description",
            }, {
                "identifier": "boolparam",
                "name": "boolean parameter",
                "type": "parameter",
                "parameterType": "boolean",
                "description": "boolean parameter description"
            }, {
                "identifier": "intparam",
                "name": "int parameter",
                "description": "int parameter description",
                "type": "parameter",
                "parameterType": "int"
            }, {
                "identifier": "floatparam",
                "name": "float parameter",
                "description": "float parameter description",
                "type": "parameter",
                "parameterType": "float"
            }, {
                "identifier": "dateparam",
                "name": "date parameter",
                "description": "date parameter description",
                "type": "parameter",
                "parameterType": "float"
            }, {
                "identifier": "defaultparam",
                "name": "default parameter",
                "description": "default parameter description",
                "type": "parameter",
                "parameterType": "int",
                "default": "1"
            }, {
                "identifier": "optparam",
                "name": "options parameter",
                "description": "options parameter description",
                "type": "parameter",
                "parameterType": "int",
                "options": ["1", "2", "3"]
            }, {
                "identifier": "reqparam",
                "name": "required parameter",
                "description": "required parameter description",
                "type": "parameter",
                "parameterType": "int",
                "required": True
            }, {
                "identifier": "output",
                "name": "output",
                "description": "Sets the output file name to <filepath>",
                "type": "output"
            }]
        }
        self.arg_parser = CoReSyFArgParser(self.manifest)

    def test_basic_parse_args(self):
        command = '--input f1 --output f2 --reqparam 1'
        self.arg_parser.parse_arguments(command.split())
        self.assertEqual(self.arg_parser.bindings['input'], 'f1')
        self.assertEqual(self.arg_parser.bindings['output'], 'f2')

    def test_parse_str_param(self):
        command = '--input f1 --output f2 --strparam str --reqparam 1'
        self.arg_parser.parse_arguments(command.split())
        self.assertEqual(self.arg_parser.bindings['strparam'], 'str')

    def test_parse_true_bool_param(self):
        command = '--input f1 --output f2 --boolparam true --reqparam 1'
        self.arg_parser.parse_arguments(command.split())
        self.assertEqual(self.arg_parser.bindings['boolparam'], True)

    def test_parse_false_bool_param(self):
        command = '--input f1 --output f2 --boolparam 0 --reqparam 1'
        self.arg_parser.parse_arguments(command.split())
        self.assertEqual(self.arg_parser.bindings['boolparam'], False)
    
    def test_parse_int_param(self):
        command = '--input f1 --output f2 --intparam 3 --reqparam 1'
        self.arg_parser.parse_arguments(command.split())
        self.assertEqual(self.arg_parser.bindings['intparam'], 3)

    def test_parse_float_param(self):
        command = '--input f1 --output f2 --floatparam 0.5 --reqparam 1'
        self.arg_parser.parse_arguments(command.split())
        self.assertEqual(self.arg_parser.bindings['floatparam'], 0.5)

    def test_parse_default_param(self):
        command = '--input f1 --output f2 --reqparam 1'
        self.arg_parser.parse_arguments(command.split())
        self.assertEqual(self.arg_parser.bindings['defaultparam'], 1)

    def test_parse_opt_param(self):
        command = '--input f1 --output f2 --reqparam 1 --optparam 2'
        self.arg_parser.parse_arguments(command.split())
        self.assertEqual(self.arg_parser.bindings['optparam'], 2)

