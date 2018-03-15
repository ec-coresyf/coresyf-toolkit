import os
from unittest import TestCase
from ..packager import Packager, ToolDirectoryNotFoundException, TargetDirectoryNotFoundException, MissingRunFileException, MissingManifestFileException, MissingExamplesFileException, ToolErrorsException
from zipfile import ZipFile
from sarge import run

class TestPackager(TestCase):

    def setUp(self):
        self.scihub_credentials = ('rccc', 'ssdh2dme')

    def test_tool_dir_not_found(self):
        packager = Packager('non_existing_dir', '.', self.scihub_credentials)
        with self.assertRaises(ToolDirectoryNotFoundException):
            packager._check_tool_directory_structure()

    def test_target_dir_not_found(self):
        packager = Packager('.', 'non_existing_target', self.scihub_credentials)
        with self.assertRaises(TargetDirectoryNotFoundException):
            packager._check_tool_directory_structure()

    def test_missing_run_file(self):
        packager = Packager('./coresyftools/tests/tool1/', '.', self.scihub_credentials)
        with self.assertRaises(MissingRunFileException):
            packager._check_tool_directory_structure()

    def test_missing_manifest_file(self):
        packager = Packager('./coresyftools/tests/tool2/', '.', self.scihub_credentials)
        with self.assertRaises(MissingManifestFileException):
            packager._check_tool_directory_structure()

    def test_missing_examples_file(self):
        packager = Packager('./coresyftools/tests/tool3/', '.', self.scihub_credentials)
        with self.assertRaises(MissingExamplesFileException):
            packager._check_tool_directory_structure()

    def test_faling_test(self):
        packager = Packager('./coresyftools/tests/dummy_tool/', '.', self.scihub_credentials)
        with self.assertRaises(ToolErrorsException):
            packager.pack_tool()

    def test_successful_packing(self):
        packager = Packager('./coresyftools/tests/tool4/',
                            './coresyftools/tests/target', self.scihub_credentials)
        packager.pack_tool()
        self.assertTrue(
            os.path.exists('./coresyftools/tests/target/Dummy Tool.zip'))
        zipfile = ZipFile('./coresyftools/tests/target/Dummy Tool.zip')
        fileset = set(zipfile.namelist())
        print(fileset)
        self.assertTrue('run' in fileset)
        self.assertTrue('manifest.json' in fileset)
        self.assertTrue('examples.sh' in fileset)

    def test_package_command(self):
        cur_dir = os.getcwd()
        os.chdir('./coresyftools/tests/tool4')
        run('../../packager.py --scihub_user rccc --scihub_pass ssdh2dme')
        self.assertTrue(
            os.path.exists('../Dummy Tool.zip'))
        zipfile = ZipFile('../Dummy Tool.zip')
        fileset = set(zipfile.namelist())
        print(fileset)
        self.assertTrue('run' in fileset)
        self.assertTrue('manifest.json' in fileset)
        self.assertTrue('examples.sh' in fileset)
        os.remove('../Dummy Tool.zip')
        os.chdir(cur_dir)

    def test_package_command_with_opts(self):
        cur_dir = os.getcwd()
        os.chdir('./coresyftools')
        run('./packager.py --tool_dir=./tests/tool4 --target_dir=./tests/target --scihub_user rccc --scihub_pass ssdh2dme')
        self.assertTrue(
            os.path.exists('./tests/target/Dummy Tool.zip'))
        zipfile = ZipFile('./tests/target/Dummy Tool.zip')
        fileset = set(zipfile.namelist())
        print(fileset)
        self.assertTrue('run' in fileset)
        self.assertTrue('manifest.json' in fileset)
        self.assertTrue('examples.sh' in fileset)
        os.remove('./tests/target/Dummy Tool.zip')
        os.chdir(cur_dir)
