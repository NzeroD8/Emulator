import base64
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from emulator import (
    EmulatorApp,
    define_vfs_name,
    parse_em_args,
    parse_input,
    read_script_lines,
)
from vfs import load_vfs


class ParseInputTestCase(unittest.TestCase):

    def test_command_with_args(self):
        """Команда с несколькими аргументами разбирается верно."""
        command, args = parse_input("ls -la /home")
        self.assertEqual(command, "ls")
        self.assertEqual(args, ["-la", "/home"])

    def test_command_without_args(self):
        """Команда без аргументов возвращает пустой список args."""
        command, args = parse_input("cd")
        self.assertEqual(command, "cd")
        self.assertEqual(args, [])

    def test_empty_input(self):
        """Пустая строка даёт пустую команду."""
        command, args = parse_input("   ")
        self.assertEqual(command, "")
        self.assertEqual(args, [])

    def test_extra_whitespace_is_ignored(self):
        """Лишние пробелы не влияют на разбор."""
        command, args = parse_input("  cd    /var/log  ")
        self.assertEqual(command, "cd")
        self.assertEqual(args, ["/var/log"])


class ParseCliArgsTestCase(unittest.TestCase):

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
        """Имя VFS берётся из имени файла без расширения."""
        self.assertEqual(define_vfs_name("/home/user/my_vfs.json"), "my_vfs")

    def test_default_name_when_path_missing(self):
        """При отсутствии пути возвращается имя по умолчанию."""
        self.assertEqual(define_vfs_name(None), "VFS")

    def test_name_without_extension(self):
        """Путь без расширения тоже даёт корректное имя."""
        self.assertEqual(define_vfs_name("noext"), "noext")


class ReadScriptLinesTestCase(unittest.TestCase):

    def test_comments_and_blank_lines_are_skipped(self):
        """Комментарии и пустые строки исключаются из результата."""
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
        """Отсутствующий файл скрипта вызывает OSError."""
        with self.assertRaises(OSError):
            read_script_lines("/path/does/not/exist.txt")


def _write_vfs_json(data):
    """Записывает словарь во временный JSON-файл VFS и возвращает путь."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp_file:
        json.dump(data, tmp_file)
        return tmp_file.name


def _b64(text):
    """Кодирует строку в base64 для вставки в JSON-описание VFS."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _build_deep_vfs_file():
    """Создаёт временный JSON с VFS вложенностью в 3 уровня и возвращает путь."""
    data = {
        "name": "deep_vfs",
        "children": [
            {"name": "top_file.txt", "type": "file",
             "content_base64": _b64("top")},
            {"name": "level1", "type": "dir", "children": [
                {"name": "sibling.txt", "type": "file",
                 "content_base64": _b64("sib")},
                {"name": "level2", "type": "dir", "children": [
                    {"name": "level3", "type": "dir", "children": [
                        {"name": "deep_file.txt", "type": "file",
                         "content_base64": _b64("deep")}
                    ]}
                ]}
            ]},
        ],
    }
    return _write_vfs_json(data)


class CommandsTestCase(unittest.TestCase):

    def setUp(self):
        """Готовит EmulatorApp с загруженной VFS, но без реального окна."""
        self.vfs_path = _build_deep_vfs_file()
        self.app = EmulatorApp.__new__(EmulatorApp)
        self.app.logs = []
        self.app.write_output = self.app.logs.append
        self.app.vfs_root, self.app.vfs_name, self.app.vfs_hash = load_vfs(
            self.vfs_path
        )
        self.app.dir_stack = [self.app.vfs_root]
        self.app.start_time = time.monotonic()

    def tearDown(self):
        """Удаляет временный файл VFS после каждого теста."""
        os.remove(self.vfs_path)

    def run_command(self, raw_line):
        """Разбирает и выполняет одну команду, возвращая строки лога."""
        self.app.logs.clear()
        command, args = parse_input(raw_line)
        {
            "ls": lambda: self.app._cmd_ls(args),
            "cd": lambda: self.app._cmd_cd(args),
            "pwd": lambda: self.app._cmd_pwd(),
            "tree": lambda: self.app._cmd_tree(),
            "uptime": lambda: self.app._cmd_uptime(),
            "chown": lambda: self.app._cmd_chown(args),
            "rm": lambda: self.app._cmd_rm(args),
        }[command]()
        return self.app.logs

    def test_pwd_at_root(self):
        """В корне VFS pwd возвращает '/'."""
        self.assertEqual(self.run_command("pwd"), ["/"])

    def test_ls_at_root_lists_children_sorted(self):
        """ls в корне перечисляет детей по алфавиту, папки с '/'."""
        self.assertEqual(
            self.run_command("ls"), ["level1/  top_file.txt"]
        )

    def test_cd_into_subdirectory_and_back(self):
        """cd в поддиректорию и обратно через .. меняет текущий путь."""
        self.run_command("cd level1")
        self.assertEqual(self.run_command("pwd"), ["/level1"])
        self.run_command("cd ..")
        self.assertEqual(self.run_command("pwd"), ["/"])

    def test_cd_multiple_levels_deep(self):
        """Последовательные cd позволяют спуститься на 3 уровня вниз."""
        self.run_command("cd level1")
        self.run_command("cd level2")
        self.run_command("cd level3")
        self.assertEqual(self.run_command("pwd"), ["/level1/level2/level3"])
        self.assertEqual(self.run_command("ls"), ["deep_file.txt"])

    def test_cd_up_past_root_stays_at_root(self):
        """cd .. в корне не вызывает ошибку и остаётся в корне."""
        self.run_command("cd ..")
        self.assertEqual(self.run_command("pwd"), ["/"])

    def test_cd_missing_directory_reports_error(self):
        """cd в несуществующую директорию выводит ошибку."""
        result = self.run_command("cd no_such_dir")
        self.assertEqual(
            result, ["cd: нет такого файла или директории: no_such_dir"]
        )

    def test_cd_into_file_reports_error(self):
        """cd в путь, указывающий на файл, выводит ошибку."""
        result = self.run_command("cd top_file.txt")
        self.assertEqual(
            result, ["cd: не является директорией: top_file.txt"]
        )

    def test_ls_missing_path_reports_error(self):
        """ls с несуществующим путём выводит ошибку."""
        result = self.run_command("ls no_such_path")
        self.assertEqual(
            result, ["ls: нет такого файла или директории: no_such_path"]
        )

    def test_ls_on_file_prints_file_name(self):
        """ls, указывающий на файл, печатает только его имя."""
        self.assertEqual(self.run_command("ls top_file.txt"), ["top_file.txt"])

    def test_tree_shows_full_nested_structure(self):
        """tree строит вложенную структуру с отступами по уровням."""
        result = self.run_command("tree")
        expected = (
            "deep_vfs/\n"
            "  level1/\n"
            "    level2/\n"
            "      level3/\n"
            "        deep_file.txt\n"
            "    sibling.txt\n"
            "  top_file.txt"
        )
        self.assertEqual(result, [expected])

    def test_uptime_is_non_negative_number(self):
        """uptime возвращает неотрицательное число секунд."""
        result = self.run_command("uptime")
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith("uptime: "))

    def test_chown_on_file_changes_owner(self):
        """chown меняет владельца файла в памяти."""
        result = self.run_command("chown top_file.txt alice")
        self.assertEqual(result, ["chown: top_file.txt -> alice"])
        target = self.app.vfs_root.find_child("top_file.txt")
        self.assertEqual(target.owner, "alice")

    def test_chown_on_directory_changes_owner(self):
        """chown меняет владельца директории в памяти."""
        result = self.run_command("chown level1 carol")
        self.assertEqual(result, ["chown: level1 -> carol"])
        target = self.app.vfs_root.find_child("level1")
        self.assertEqual(target.owner, "carol")

    def test_chown_missing_path_reports_error(self):
        """chown с несуществующим путём выводит ошибку."""
        result = self.run_command("chown no_such.txt alice")
        self.assertEqual(
            result, ["chown: нет такого файла или директории: no_such.txt"]
        )

    def test_chown_wrong_number_of_args_reports_usage(self):
        """chown без владельца выводит подсказку по использованию."""
        result = self.run_command("chown top_file.txt")
        self.assertEqual(
            result, ["chown: использование: chown <путь> <владелец>"]
        )

    def test_rm_removes_file(self):
        """rm удаляет файл из родительской директории."""
        result = self.run_command("rm top_file.txt")
        self.assertEqual(result, ["rm: удалён top_file.txt"])
        self.assertIsNone(self.app.vfs_root.find_child("top_file.txt"))

    def test_rm_removes_subdirectory_with_contents(self):
        """rm удаляет директорию вместе со всем её содержимым."""
        result = self.run_command("rm level1/level2")
        self.assertEqual(result, ["rm: удалён level1/level2"])
        level1 = self.app.vfs_root.find_child("level1")
        self.assertIsNone(level1.find_child("level2"))

    def test_rm_missing_path_reports_error(self):
        """rm с несуществующим путём выводит ошибку."""
        result = self.run_command("rm no_such.txt")
        self.assertEqual(
            result, ["rm: нет такого файла или директории: no_such.txt"]
        )

    def test_rm_without_args_reports_usage(self):
        """rm без аргумента выводит подсказку."""
        result = self.run_command("rm")
        self.assertEqual(
            result, ["rm: укажите путь к файлу или директории"]
        )

    def test_rm_parent_directory_reference_reports_error(self):
        """rm '..' отклоняется как недопустимая цель."""
        result = self.run_command("rm ..")
        self.assertEqual(result, ["rm: нельзя применить команду к '..'"])


class CommandsWithoutVfsTestCase(unittest.TestCase):

    def setUp(self):
        """Готовит EmulatorApp без загруженной VFS."""
        self.app = EmulatorApp.__new__(EmulatorApp)
        self.app.logs = []
        self.app.write_output = self.app.logs.append
        self.app.vfs_root = None
        self.app.dir_stack = None
        self.app.start_time = time.monotonic()

    def run_command(self, raw_line):
        """Разбирает и выполняет одну команду, возвращая строки лога."""
        self.app.logs.clear()
        command, args = parse_input(raw_line)
        {
            "ls": lambda: self.app._cmd_ls(args),
            "cd": lambda: self.app._cmd_cd(args),
            "pwd": lambda: self.app._cmd_pwd(),
            "tree": lambda: self.app._cmd_tree(),
            "uptime": lambda: self.app._cmd_uptime(),
            "chown": lambda: self.app._cmd_chown(args),
            "rm": lambda: self.app._cmd_rm(args),
        }[command]()
        return self.app.logs

    def test_ls_without_vfs_reports_error(self):
        """ls без загруженной VFS сообщает об ошибке."""
        self.assertEqual(self.run_command("ls"), ["Ошибка: VFS не загружена"])

    def test_cd_without_vfs_reports_error(self):
        """cd без загруженной VFS сообщает об ошибке."""
        self.assertEqual(
            self.run_command("cd foo"), ["Ошибка: VFS не загружена"]
        )

    def test_pwd_without_vfs_reports_error(self):
        """pwd без загруженной VFS сообщает об ошибке."""
        self.assertEqual(self.run_command("pwd"), ["Ошибка: VFS не загружена"])

    def test_tree_without_vfs_reports_error(self):
        """tree без загруженной VFS сообщает об ошибке."""
        self.assertEqual(
            self.run_command("tree"), ["Ошибка: VFS не загружена"]
        )

    def test_uptime_works_without_vfs(self):
        """uptime не зависит от VFS и работает всегда."""
        result = self.run_command("uptime")
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith("uptime: "))

    def test_chown_without_vfs_reports_error(self):
        """chown без загруженной VFS сообщает об ошибке."""
        self.assertEqual(
            self.run_command("chown foo alice"), ["Ошибка: VFS не загружена"]
        )

    def test_rm_without_vfs_reports_error(self):
        """rm без загруженной VFS сообщает об ошибке."""
        self.assertEqual(
            self.run_command("rm foo"), ["Ошибка: VFS не загружена"]
        )


if __name__ == "__main__":
    unittest.main()
