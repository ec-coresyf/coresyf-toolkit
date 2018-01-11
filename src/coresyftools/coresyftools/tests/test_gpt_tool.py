from unittest import TestCase
import json
import os

from gpt_coresyf_tool import GPTCoReSyFTool


class TestGPTTool(TestCase):

    def setUp(self):
        self.manifest = {
            'name': 'dummy tool',
            'arguments': [
                {
                    'identifier': 'Ssource',
                    'name': 'input',
                    'description': 'description',
                    'type': 'data'
                },
                {
                    'identifier': 'Ttarget',
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

    def write_manifest(self, manifest):
        with open('manifest.json', 'w') as manifest_file:
            json.dump(manifest, manifest_file)
        self.runfile = os.path.join(os.getcwd(), 'run')

    def rm_manifest(self):
        os.remove('manifest.json')

    def test_atomic_command(self):
        manifest = self.manifest.copy()
        manifest['operation'] = {'operation': 'LandSeaMask'}
        self.write_manifest(manifest)
        tool = GPTCoReSyFTool(self.runfile)

        class CallShellCommandMock():
            def __call__(self, args):
                self.args = args

        call_shell_command_mock = CallShellCommandMock()

        tool._call_shell_command = call_shell_command_mock

        with open('input', 'w') as infile:
            infile.write('input')

        cmd = '--Ssource input --Ttarget output --param val'.split()
        tool.execute(cmd)

        gpt_cmd = 'gpt LandSeaMask -f GeoTIFF-BigTIFF -t {} -param=val {}'.format(
            os.path.join(os.getcwd(), 'output'), os.path.join(os.getcwd(), 'input')).split()
        self.assertEqual(call_shell_command_mock.args, gpt_cmd)

    def test_graph(self):
        pass

    def test_missing_operation_and_graph(self):
        pass

    def test_missing_graph(self):
        pass
