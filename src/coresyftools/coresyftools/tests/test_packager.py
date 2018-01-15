import os
from unittest import TestCase
from ..packager import Packager, ToolDirectoryNotFoundException, TargetDirectoryNotFoundException, MissingRunFileException, MissingManifestFileException, MissingExamplesFileException, ToolErrorsException
from zipfile import ZipFile

class TestPackager(TestCase):

    def test_tool_dir_not_found(self):
        packager = Packager('non_existing_dir', '.')
        with self.assertRaises(ToolDirectoryNotFoundException):
            packager._check_tool_directory_structure()

    def test_target_dir_not_found(self):
        packager = Packager('.', 'non_existing_target')
        with self.assertRaises(TargetDirectoryNotFoundException):
            packager._check_tool_directory_structure()

    def test_missing_run_file(self):
        packager = Packager('./coresyftools/tests/tool1/', '.')
        with self.assertRaises(MissingRunFileException):
            packager._check_tool_directory_structure()

    def test_missing_manifest_file(self):
        packager = Packager('./coresyftools/tests/tool2/', '.')
        with self.assertRaises(MissingManifestFileException):
            packager._check_tool_directory_structure()

    def test_missing_examples_file(self):
        packager = Packager('./coresyftools/tests/tool3/', '.')
        with self.assertRaises(MissingExamplesFileException):
            packager._check_tool_directory_structure()

    def test_faling_test(self):
        packager = Packager('./coresyftools/tests/dummy_tool/', '.')
        with self.assertRaises(ToolErrorsException):
            packager.pack_tool()

    def test_successful_packing(self):
        packager = Packager('./coresyftools/tests/tool4/',
                            './coresyftools/tests/target')
        packager.pack_tool()
        self.assertTrue(
            os.path.exists('./coresyftools/tests/target/Dummy Tool.zip'))
        zipfile = ZipFile('./coresyftools/tests/target/Dummy Tool.zip')
        fileset = set(zipfile.namelist())
        print(fileset)
        self.assertTrue('run' in fileset)
        self.assertTrue('manifest.json' in fileset)
        self.assertTrue('examples.sh' in fileset)

        

