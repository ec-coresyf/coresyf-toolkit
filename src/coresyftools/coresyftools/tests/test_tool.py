from unittest import TestCase
import os
from zipfile import ZipFile

from ..tool import CoReSyFTool, EmptyOutputFile, NoOutputFile

import json


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
