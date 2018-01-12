from unittest import TestCase

from ..tool_tester import ToolTester, NonZeroReturnCode, NonEmptyStderr, NoOutputFile, EmptyOutputFile


class TestTester(TestCase):

    def test_tester(self):
        tester = ToolTester('coresyftools/tests/dummy_tool')
        tester.test()
        print(tester.errors)
        self.assertEqual(len(tester.errors), 4)
        self.assertIsInstance(tester.errors[0], NonZeroReturnCode)
        self.assertEqual(tester.errors[0].returncode, 1)
        self.assertIsNotNone(tester.errors[0].stderr)
        self.assertIsInstance(tester.errors[1], NonEmptyStderr)
        self.assertIsInstance(tester.errors[2], NonZeroReturnCode)
        self.assertIsInstance(tester.errors[3], NonZeroReturnCode)
