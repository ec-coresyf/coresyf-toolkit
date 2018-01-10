from unittest import TestCase

from tool_tester import ToolTester


class TestTester(TestCase):

    def test_tester(self):
        tester = ToolTester('tests/dummy_tool')
        tester.test()
        self.assertEqual(len(tester.errors), 4)
        self.assertEqual(tester.errors[0].returncode, 1)
        self.assertIsNotNone(tester.errors[0].stderr)
        self.assertEqual(tester.errors[1].message, 'stderrmsg')
        self.assertEqual(tester.errors[2].file, 'void_output')
        self.assertEqual(tester.errors[3].file, 'empty_output')
