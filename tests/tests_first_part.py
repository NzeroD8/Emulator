import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from emulator import (  # noqa: E402
    EmulatorApp,
    define_vfs_name,
    parse_em_args,
    parse_input,
    read_script_lines,
)


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


class FormatOutputTestCase(unittest.TestCase):

    def setUp(self):
        self.app = EmulatorApp.__new__(EmulatorApp)

    def test_stub_with_args(self):
        result = self.app._format_output("ls", ["-la", "/home"])
        self.assertEqual(result, "ls: -la /home")

    def test_stub_without_args(self):
        result = self.app._format_output("cd", [])
        self.assertEqual(result, "cd: (без аргументов)")


class ParseCliArgsTestCase(unittest.TestCase):
    """Тесты для разбора параметров командной строки."""

    def test_both_params_provided(self):
        """Оба параметра распознаются корректно."""
        args = parse_em_args(
            ["--vfs-path", "/tmp/my_vfs.json", "--script", "/tmp/s.txt"]
        )
        self.assertEqual(args.vfs_path, "/tmp/my_vfs.json")
        self.assertEqual(args.script_path, "/tmp/s.txt")

    def test_no_params_provided(self):
        """Отсутствие параметров даёт значения None по умолчанию."""
        args = parse_em_args([])
        self.assertIsNone(args.vfs_path)
        self.assertIsNone(args.script_path)

    def test_only_vfs_path_provided(self):
        """Указание только пути к VFS не требует пути к скрипту."""
        args = parse_em_args(["--vfs-path", "/tmp/my_vfs.json"])
        self.assertEqual(args.vfs_path, "/tmp/my_vfs.json")
        self.assertIsNone(args.script_path)


class DefineVfsNameTestCase(unittest.TestCase):

    def test_name_from_path(self):
        self.assertEqual(define_vfs_name("/home/user/my_vfs.json"), "my_vfs")

    def test_default_name_when_path_missing(self):
        self.assertEqual(define_vfs_name(None), "VFS")

    def test_name_without_extension(self):
        self.assertEqual(define_vfs_name("noext"), "noext")


class ReadScriptLinesTestCase(unittest.TestCase):

    def test_comments_and_blank_lines_are_skipped(self):
        script_text = (
            "# комментарий\n"
            "ls -la /home\n"
            "\n"
            "cd /var/log\n"
            "# ещё комментарий\n"
            "exit\n"
        )
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(script_text)
            tmp_path = tmp_file.name
        try:
            lines = read_script_lines(tmp_path)
        finally:
            os.remove(tmp_path)
        self.assertEqual(lines, ["ls -la /home", "cd /var/log", "exit"])

    def test_missing_file_raises_oserror(self):
        with self.assertRaises(OSError):
            read_script_lines("/path/does/not/exist.txt")


if __name__ == "__main__":
    unittest.main()
