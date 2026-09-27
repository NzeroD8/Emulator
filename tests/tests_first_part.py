import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "src"))

from emulator import parse_input, EmulatorApp


class ParseInputTestCase(unittest.TestCase):

    def test_command_with_args(self):
        command, args = parse_input("ls -la /home")
        self.assertEqual(command, "ls")
        self.assertEqual(args, ["-la", "/home"])

    def test_command_without_args(self):
        command, args = parse_input("cd")
        self.assertEqual(command, "cd")
        self.assertEqual(args, [])

    def test_empty_input(self):
        command, args = parse_input("   ")
        self.assertEqual(command, "")
        self.assertEqual(args, [])

    def test_extra_whitespace_is_ignored(self):
        command, args = parse_input("  cd    /var/log  ")
        self.assertEqual(command, "cd")
        self.assertEqual(args, ["/var/log"])


class FormatStubOutputTestCase(unittest.TestCase):

    def setUp(self):
        self.app = EmulatorApp.__new__(EmulatorApp)

    def test_stub_with_args(self):
        result = self.app._format_output("ls", ["-la", "/home"])
        self.assertEqual(result, "ls: -la /home")

    def test_stub_without_args(self):
        result = self.app._format_output("cd", [])
        self.assertEqual(result, "cd: (без аргументов)")


if __name__ == "__main__":
    unittest.main()
