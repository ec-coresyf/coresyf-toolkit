from unittest import TestCase
import json
import os

from ..gpt_coresyf_tool import GPTCoReSyFTool, GPTGraphFileNotFound
from ..coresyf_manifest import InvalidManifestException


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
        with open('output', 'w') as output:
            output.write('output')
    
    def tearDown(self):
        self.rm_manifest()
        os.remove('output')

    def write_manifest(self, manifest):
        with open('manifest.json', 'w') as manifest_file:
            json.dump(manifest, manifest_file)
        self.runfile = os.path.join(os.getcwd(), 'run')

    def rm_manifest(self):
        os.remove('manifest.json')

    def test_atomic_command(self):
        manifest = self.manifest.copy()
        manifest['operation'] = {'operation': 'Land-Sea-Mask'}
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

        gpt_cmd = 'gpt Land-Sea-Mask -f GeoTIFF-BigTIFF -t {} -param=val {}'.format(
            os.path.join(os.getcwd(), 'output'), os.path.join(os.getcwd(), 'input')).split()
        self.assertEqual(call_shell_command_mock.args, gpt_cmd)
        os.remove('input')

    def test_graph(self):
        manifest = self.manifest.copy()
        manifest['operation'] = {'graph': True}
        self.write_manifest(manifest)

        with open('gpt_graph.xml', 'w'):
            pass

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

        gpt_cmd = 'gpt {} -f GeoTIFF-BigTIFF -t {} -param=val {}'.format(
            os.path.join(os.getcwd(), 'gpt_graph.xml'),
            os.path.join(os.getcwd(), 'output'), os.path.join(os.getcwd(), 'input')).split()
        self.assertEqual(call_shell_command_mock.args, gpt_cmd)
        os.remove('input')
        os.remove('gpt_graph.xml')

    def test_missing_operation_and_graph(self):
        manifest = self.manifest.copy()
        self.write_manifest(manifest)
        self.assertRaises(InvalidManifestException,
                          lambda: GPTCoReSyFTool(self.runfile))

    def test_graph_not_found(self):
        manifest = self.manifest.copy()
        manifest['operation'] = {'graph': True}
        self.write_manifest(manifest)
        self.assertRaises(GPTGraphFileNotFound,
                          lambda: GPTCoReSyFTool(self.runfile))

    def test_atomic_command_with_constant_parameters(self):
        manifest = self.manifest.copy()
        manifest['operation'] = {
                                    'operation': 'Land-Sea-Mask',
                                    'parameters': {
                                        'const': 1,
                                        'opt': 'a'
                                    }
                                }
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

        gpt_cmd = 'gpt Land-Sea-Mask -f GeoTIFF-BigTIFF -t {} -opt=a -const=1 -param=val {}'.format(
            os.path.join(os.getcwd(), 'output'), os.path.join(os.getcwd(), 'input')).split()
        self.assertEqual(call_shell_command_mock.args, gpt_cmd)
        os.remove('input')

