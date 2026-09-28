import base64
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from vfs import (
    VfsNode,
    compute_sha256,
    load_vfs,
)


def _write_json(data):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp_file:
        json.dump(data, tmp_file)
        return tmp_file.name


class VfsNodeTestCase(unittest.TestCase):

    def test_is_dir_and_is_file(self):
        """Тип узла корректно определяется методами is_dir/is_file."""
        file_node = VfsNode("a.txt", "file", content=b"data")
        dir_node = VfsNode("dir", "dir", children=[file_node])
        self.assertTrue(file_node.is_file())
        self.assertFalse(file_node.is_dir())
        self.assertTrue(dir_node.is_dir())
        self.assertFalse(dir_node.is_file())

    def test_find_child_found_and_missing(self):
        """find_child находит существующего потомка и не находит чужого."""
        child = VfsNode("child.txt", "file", content=b"x")
        parent = VfsNode("parent", "dir", children=[child])
        self.assertIs(parent.find_child("child.txt"), child)
        self.assertIsNone(parent.find_child("missing.txt"))


class ComputeSha256TestCase(unittest.TestCase):

    def test_known_hash_value(self):
        """Хеш пустой байтовой строки совпадает с ожидаемым значением."""
        expected = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        self.assertEqual(compute_sha256(b""), expected)

    def test_different_content_different_hash(self):
        """Разное содержимое даёт разные хеши."""
        self.assertNotEqual(compute_sha256(b"a"), compute_sha256(b"b"))


class LoadVfsTestCase(unittest.TestCase):

    def test_load_minimal_vfs(self):
        """Минимальная VFS загружается без ошибок."""
        path = _write_json({"name": "minimal", "children": []})
        try:
            root, name, digest = load_vfs(path)
        finally:
            os.remove(path)
        self.assertEqual(name, "minimal")
        self.assertEqual(root.children, [])
        self.assertEqual(len(digest), 64)

    def test_load_nested_vfs_and_decode_content(self):
        """Вложенные директории и base64-содержимое разбираются верно."""
        encoded = base64.b64encode(b"hello").decode()
        data = {
            "name": "nested",
            "children": [
                {
                    "name": "sub",
                    "type": "dir",
                    "children": [
                        {
                            "name": "file.txt",
                            "type": "file",
                            "content_base64": encoded,
                        }
                    ],
                }
            ],
        }
        path = _write_json(data)
        try:
            root, _, _ = load_vfs(path)
        finally:
            os.remove(path)
        sub = root.find_child("sub")
        self.assertIsNotNone(sub)
        self.assertTrue(sub.is_dir())
        file_node = sub.find_child("file.txt")
        self.assertIsNotNone(file_node)
        self.assertEqual(file_node.content, b"hello")

    def test_hash_is_stable_across_loads(self):
        """Повторная загрузка того же файла даёт одинаковый хеш."""
        path = _write_json({"name": "stable", "children": []})
        try:
            _, _, digest_1 = load_vfs(path)
            _, _, digest_2 = load_vfs(path)
        finally:
            os.remove(path)
        self.assertEqual(digest_1, digest_2)

    def test_missing_file_raises_oserror(self):
        """Отсутствующий файл VFS вызывает OSError."""
        with self.assertRaises(OSError):
            load_vfs("/path/does/not/exist_vfs.json")

    def test_invalid_json_raises_value_error(self):
        """Некорректный JSON вызывает ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write("{not valid json")
            path = tmp_file.name
        try:
            with self.assertRaises(ValueError):
                load_vfs(path)
        finally:
            os.remove(path)

    def test_invalid_base64_raises_value_error(self):
        """Некорректные base64-данные файла вызывают ValueError."""
        data = {
            "name": "bad",
            "children": [
                {
                    "name": "bad.txt",
                    "type": "file",
                    "content_base64": "not_valid_base64!!",
                }
            ],
        }
        path = _write_json(data)
        try:
            with self.assertRaises(ValueError):
                load_vfs(path)
        finally:
            os.remove(path)

    def test_missing_name_raises_value_error(self):
        """Узел без имени считается некорректным и вызывает ValueError."""
        data = {
            "name": "root",
            "children": [{"type": "file", "content_base64": ""}],
        }
        path = _write_json(data)
        try:
            with self.assertRaises(ValueError):
                load_vfs(path)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
