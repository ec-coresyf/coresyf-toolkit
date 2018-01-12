from unittest import TestCase

from ..tool_tester import ToolTester, NonZeroReturnCode, NonEmptyStderr, NoOutputFile, EmptyOutputFile


class TestTester(TestCase):

    def test_tester(self):
        tester = ToolTester('coresyftools/tests/dummy_tool')
        tester.test()
        self.assertEqual(len(tester.errors), 4)
        self.assertIsInstance(tester.errors[0], NonZeroReturnCode)
        self.assertEqual(tester.errors[0].returncode, 1)
        self.assertIsNotNone(tester.errors[0].stderr)
        self.assertIsInstance(tester.errors[1], NonEmptyStderr)
        self.assertEqual(tester.errors[1].message, 'stderrmsg')
        self.assertIsInstance(tester.errors[2], NoOutputFile)
        self.assertEqual(tester.errors[2].file, 'void_output')
        self.assertIsInstance(tester.errors[3], EmptyOutputFile)
        self.assertEqual(tester.errors[3].file, 'empty_output')
