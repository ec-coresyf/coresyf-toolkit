from unittest import TestCase
import os

from coresyf_tool_base import CoReSyFTool


class TestCoReSyFTool(TestCase):

    def setUp(self):
        self.manifest = {
            'name': 'dummy tool',
            'arguments': [
                {
                    'identifier': 'input',
                    'name': 'input',
                    'description': 'description',
                    'type': 'data'
                },
                {
                    'identifier': 'output',
                    'name': 'output',
                    'description': 'description',
                    'type': 'output'
                },
                {
                    'identifier': 'param',
                    'name': 'param',
                    'description': 'description',
                    'type': 'parameter',
                    'parameterType': 'string'
                }
            ]
        }

    def test_nominal_execution(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings

        tool = MockCoReSyFTool(manifest=self.manifest)

        with open('f1', 'w') as f1:
            f1.write('input')

        cmd = '--input f1 --output f2 --param astr'.split()
        tool.execute(cmd)
        self.assertEqual(
            tool.bindings, {'input': 'f1', 'output': 'f2', 'param': 'astr'})
        os.remove('f1')

    def test_non_existent_input(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings

        tool = MockCoReSyFTool(manifest=self.manifest)
        cmd = '--input f --output f2 --param astr'.split()
        self.assertRaises(SystemExit, lambda: tool.execute(cmd))

    def test_zip_input(self):
        pass

    def test_empty_zip_input(self):
        pass

    def test_temporary_data_cleaning(self):
        pass

    def test_no_output(self):
        pass

    def test_empty_output(self):
        pass
