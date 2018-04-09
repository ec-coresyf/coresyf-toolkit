import json
import os
from unittest import TestCase
from zipfile import ZipFile
from pathlib import Path

from ..tool import (CoReSyFTool, EmptyOutputFile,
                    MissingCommandPlaceholderForOption, NoOutputFile,
                    UnexpectedCommandPlaceholder)


class TestCoReSyFTool(TestCase):

    def setUp(self):
        self.manifest = {
            'name': 'dummy tool',
            'type': "Dummy",
            'inputs': [
                {
                    'identifier': 'input',
                    'name': 'input',
                    'description': 'description',
                }],
            'outputs': [
                {
                    'identifier': 'output',
                    'name': 'output',
                    'description': 'description',
                }],
            'parameters': [
                {
                    'identifier': 'param',
                    'name': 'param',
                    'description': 'description',
                    'type': 'string'
                }
            ]
        }
        with open('manifest.json', 'w') as manifest_file:
            json.dump(self.manifest, manifest_file)
        self.runfile = os.path.join(os.getcwd(), 'run')

    def tearDown(self):
        os.remove('manifest.json')

    def test_nominal_execution(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings
                with open('f2', 'w') as out:
                    out.write('output')

        tool = MockCoReSyFTool(self.runfile)

        with open('f1', 'w') as f1:
            f1.write('input')

        cmd = '--input f1 --output f2 --param astr'.split()
        tool.execute(cmd)
        self.assertEqual(
            tool.bindings, {'input': 'f1', 'output': 'f2', 'param': 'astr'})
        os.remove('f1')
        os.remove('f2')

    def test_collection_input(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings
                with open('f2', 'w') as out:
                    out.write('output')

        manifest = self.manifest.copy()
        manifest['inputs'] = [
            {
                'identifier': 'input',
                'name': 'input',
                'description': 'desc',
                'collection': True
            }
        ]
        with open('manifest.json', 'w') as manifest_file:
            json.dump(manifest, manifest_file)
        self.runfile = os.path.join(os.getcwd(), 'run')

        tool = MockCoReSyFTool(self.runfile)

        with open('f1', 'w') as f1:
            f1.write('input')
        with open('f12', 'w') as f1:
            f1.write('input')
        with open('f13', 'w') as f1:
            f1.write('input')

        cmd = '--input f1 f12 f13 --output f2 --param astr'.split()
        tool.execute(cmd)
        self.assertEqual(
            tool.bindings, {'input': ['f1', 'f12', 'f13'], 'output': 'f2', 'param': 'astr'})
        os.remove('f1')
        os.remove('f12')
        os.remove('f13')
        os.remove('f2')

        self.setUp()

    def test_collection_ouput(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings
                with open('f2', 'w') as out:
                    out.write('output')
                with open('f22', 'w') as out:
                    out.write('output')
                with open('f23', 'w') as out:
                    out.write('output')

        manifest = self.manifest.copy()
        manifest['outputs'] = [
            {
                'identifier': 'output',
                'name': 'output',
                'description': 'desc',
                'collection': True
            }
        ]
        with open('manifest.json', 'w') as manifest_file:
            json.dump(manifest, manifest_file)
        self.runfile = os.path.join(os.getcwd(), 'run')

        tool = MockCoReSyFTool(self.runfile)

        with open('f1', 'w') as f1:
            f1.write('input')

        cmd = '--input f1 --output f2 f22 f23 --param astr'.split()
        tool.execute(cmd)
        self.assertEqual(
            tool.bindings, {'input': 'f1', 'output': ['f2', 'f22', 'f23'], 'param': 'astr'})
        os.remove('f1')
        os.remove('f2')
        os.remove('f22')
        os.remove('f23')

        self.setUp()

    def test_non_existent_input(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings
                with open('f2', 'w') as out:
                    out.write('output')

        tool = MockCoReSyFTool(self.runfile)
        cmd = '--input f --output f2 --param astr'.split()
        self.assertRaises(SystemExit, lambda: tool.execute(cmd))

    def test_zip_input(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                f1 = bindings['input']
                with open(f1) as inputfile:
                    self.input_text = inputfile.read()
                    with open('f2', 'w') as out:
                        out.write('output')

        tool = MockCoReSyFTool(self.runfile)

        with open('f1', 'w') as f1:
            f1.write('input')
        with ZipFile('f1.zip', 'w') as f1zip:
            f1zip.write('f1')

        cmd = '--input f1.zip --output f2 --param astr'.split()
        tool.execute(cmd)
        self.assertEqual(tool.input_text, 'input')
        os.remove('f1.zip')
        os.remove('f1')
        os.remove('f2')

    def test_empty_zip_input(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                f1 = bindings['input']
                with open(f1) as inputfile:
                    self.input_text = inputfile.read()
                    with open('f2', 'w') as out:
                        out.write('output')

        tool = MockCoReSyFTool(self.runfile)

        with ZipFile('f1.zip', 'w'):
            pass

        cmd = '--input f1.zip --output f2 --param astr'.split()
        self.assertRaises(SystemExit, lambda: tool.execute(cmd))

    def test_temporary_data_cleaning(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                with open(os.path.join(self.get_temporary_directory(),
                                       'tempfile'), 'w'):
                    pass
                with open('f2', 'w') as out:
                    out.write('output')

        tool = MockCoReSyFTool(self.runfile)

        with open('f1', 'w') as f1:
            f1.write('input')

        cmd = '--input f1 --output f2 --param astr'.split()
        tool.execute(cmd)
        self.assertEqual(
            tool.bindings, {'input': 'f1', 'output': 'f2', 'param': 'astr'})
        os.remove('f1')
        os.remove('f2')
        self.assertFalse(os.path.exists('tmp/tempfile'))

    def test_no_output(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings

        tool = MockCoReSyFTool(self.runfile)

        with open('f1', 'w') as f1:
            f1.write('input')

        cmd = '--input f1 --output f3 --param astr'.split()
        self.assertRaises(NoOutputFile, lambda: tool.execute(cmd))
        os.remove('f1')

    def test_empty_output(self):
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings
                with open('f2', 'w'):
                    pass

        tool = MockCoReSyFTool(self.runfile)

        with open('f1', 'w') as f1:
            f1.write('input')

        cmd = '--input f1 --output f2 --param astr'.split()
        self.assertRaises(EmptyOutputFile, lambda: tool.execute(cmd))
        os.remove('f1')

    def test_can_successfully_run_command_from_interpolated_template(self):
        coresyf_tool = CoReSyFTool(self.runfile)
        (pipeline, stdout, stderr) = coresyf_tool.invoke_shell_command(
            "test {op}", op="1")
        self.assertEqual(pipeline.returncode, 0)

    def test_can_read_failed_return_code_after_running_shell_command(self):
        coresyf_tool = CoReSyFTool(self.runfile)
        (pipeline, stdout, stderr) = coresyf_tool.invoke_shell_command(
            "test {op1} = {op2}", op1="1", op2="2")
        self.assertEqual(pipeline.returncode, 1)

    def test_can_read_stdout_after_running_shell_command(self):
        coresyf_tool = CoReSyFTool(self.runfile)
        (pipeline, stdout, stderr) = coresyf_tool.invoke_shell_command("echo -n out")
        self.assertEqual(stdout.read(), 'out')

    def test_can_read_stderr_after_running_shell_command(self):
        coresyf_tool = CoReSyFTool(self.runfile)
        (pipeline, stdout, stderr) = coresyf_tool.invoke_shell_command("rm nofile")
        self.assertIn('rm: cannot remove', stderr.read())

    def _extend_manifest(self, extra_fields):
        manifest = self.manifest.copy()
        manifest.update(extra_fields)
        with open('manifest.json', 'w') as manifest_file:
            json.dump(manifest, manifest_file)
        self.runfile = os.path.join(os.getcwd(), 'run')

    def test_can_run_shell_command_of_manifest(self):
        self._extend_manifest({
            'command': 'cp {input} {output}; echo {param}'
        })
        with open('f1', 'w') as f1:
            f1.write('input')
        tool = CoReSyFTool(self.runfile)
        cmd = '--input f1 --output f2 --param astr'.split()
        tool.execute(cmd)
        self.assertTrue(os.path.exists('f2'))

    def test_can_handle_unexpected_command_placeholders(self):
        self._extend_manifest({
            'command': 'cp {input} {unexpected_placeholder}; echo {param}'
        })
        with self.assertRaises(UnexpectedCommandPlaceholder):
            CoReSyFTool(self.runfile)

    def test_can_handle_missing_command_placeholders(self):
        self._extend_manifest({
            'command': 'cp {input}'
        })
        with self.assertRaises(MissingCommandPlaceholderForOption):
            CoReSyFTool(self.runfile)

    def test_can_use_custom_manifest_name(self):
        """Test we can pass the manifest file name to CoReSyTFTool."""
        manifest = self.manifest.copy()
        manifest['name'] = 'MyFairTool'
        manifest_file_name = 'my_tool.manifest.json'
        with open(manifest_file_name, 'w') as manifest_file:
            manifest_file.write(json.dumps(manifest))
        tool = CoReSyFTool(self.runfile, manifest_file_name)
        self.assertEqual(tool.manifest_file_name,
                         str(Path(self.runfile).parent / manifest_file_name))
        self.assertEqual(tool.manifest['name'], 'MyFairTool')
        os.remove(manifest_file_name)

    def test_zip_output(self):
        """Test the method to compress an output folder"""
        tool = CoReSyFTool(self.runfile, 'manifest.json')
        tool.write_to_zipfile('coresyftools/tests/tool6/myoutput/')
        files_ = os.listdir('coresyftools/tests/tool6')
        assert 'myoutput' in files_
        archive = ZipFile('coresyftools/tests/tool6/myoutput', 'r')
        self.assertGreater(len(archive.namelist()), 0)
        archive.close()
        os.remove('coresyftools/tests/tool6/myoutput')
        os.rename('coresyftools/tests/tool6/myoutput_', 
                    'coresyftools/tests/tool6/myoutput')

    def test_zip_output_from_tool(self):
        """Test the output compression when generated by a tool"""
        class MockCoReSyFTool(CoReSyFTool):
            def run(self, bindings):
                self.run_bindings = bindings
                if not os.path.exists('mydummyoutput'):
                    os.mkdir('mydummyoutput')
                with open('mydummyoutput/f2', 'w'):
                    pass

        tool = MockCoReSyFTool(self.runfile)

        with open('f1', 'w') as f1:
            f1.write('input')

        cmd = '--input f1 --output mydummyoutput --param astr'.split()
        tool.execute(cmd)
        assert 'mydummyoutput' in os.listdir('.')
        archive = ZipFile('mydummyoutput', 'r')
        self.assertGreater(len(archive.namelist()), 0)
        archive.close()
        os.remove('f1')
        os.remove('mydummyoutput')
        os.remove('mydummyoutput_/f2')
        os.rmdir('mydummyoutput_')

