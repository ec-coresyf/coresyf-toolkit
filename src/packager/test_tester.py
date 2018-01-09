from unittest import TestCase

from tool_tester import ToolTester


class TestTester(TestCase):

    def test_tester(self):
        tester = ToolTester('./dummy_tool')
        tester.test()
        self.assertEqual(len(tester.errors), 2)
        self.assertEqual(tester.errors[0].returncode, 1)
        self.assertIsNotNone(tester.errors[0].stderr)
        self.assertEqual(tester.errors[1].message, 'stderrmsg')
