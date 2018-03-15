from unittest import TestCase

from ..tool_tester import ToolTester, NonZeroReturnCode, NonEmptyStderr, NoOutputFile, EmptyOutputFile
import os


class TestTester(TestCase):

    def test_download_input(self):
        tester = ToolTester('coresyftools/tests/dummy_tool',
                            ('rccc', 'ssdh2dme'))
        tester._download_input('downloaded_file', "https://scihub.copernicus.eu/dhus/odata/v1/Products('8be67f04-2287-40d2-b6ba-5c1bf0ff8ee1')/$value", tester.scihub_credentials)
        self.assertTrue(os.path.exists('downloaded_file'))
        self.assertGreater(os.path.getsize('downloaded_file'), 0)
        os.remove('downloaded_file')
    
    def test_inputs_mappings(self):
        tester = ToolTester('coresyftools/tests/dummy_tool',
                           ('rccc', 'ssdh2dme'))
        self.assertDictEqual(tester.input_mappings,
                            {'input': "https://scihub.copernicus.eu/dhus/odata/v1/Products('8be67f04-2287-40d2-b6ba-5c1bf0ff8ee1')/$value"})

    def test_tester(self):
        tester = ToolTester('coresyftools/tests/dummy_tool',
                            ('rccc','ssdh2dme'))
        tester.test()
        print(tester.errors)
        self.assertEqual(len(tester.errors), 4)
        self.assertIsInstance(tester.errors[0], NonZeroReturnCode)
        self.assertEqual(tester.errors[0].returncode, 1)
        self.assertIsNotNone(tester.errors[0].stderr)
        self.assertIsInstance(tester.errors[1], NonEmptyStderr)
        self.assertIsInstance(tester.errors[2], NonZeroReturnCode)
        self.assertIsInstance(tester.errors[3], NonZeroReturnCode)
