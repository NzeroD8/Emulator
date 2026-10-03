import base64
import hashlib
import json

NODE_TYPE_DIR = "dir"
NODE_TYPE_FILE = "file"
DEFAULT_VFS_DISPLAY_NAME = "Vfs"
DEFAULT_OWNER = "root"


class VfsNode:

    def __init__(self, name, node_type, content=None, children=None,
                 owner=DEFAULT_OWNER):
        self.name = name
        self.node_type = node_type
        self.content = content
        self.children = children if children is not None else []
        self.owner = owner

    def is_dir(self):
        return self.node_type == NODE_TYPE_DIR

    def is_file(self):
        return self.node_type == NODE_TYPE_FILE

    def find_child(self, name):
        for child in self.children:
            if child.name == name:
                return child
        return None


def _decode_file_content(name, encoded_content):
    try:
        return base64.b64decode(encoded_content, validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError(
            f"Некорректные base64-данные в файле '{name}': {error}"
        ) from error


def _build_node(raw_node):
    name = raw_node.get("name")
    node_type = raw_node.get("type")
    if not name or node_type not in (NODE_TYPE_DIR, NODE_TYPE_FILE):
        raise ValueError(f"Некорректный узел VFS: {raw_node!r}")

    if node_type == NODE_TYPE_FILE:
        encoded_content = raw_node.get("content_base64", "")
        content = _decode_file_content(name, encoded_content)
        return VfsNode(name, NODE_TYPE_FILE, content=content)

    raw_children = raw_node.get("children", [])
    children = [_build_node(child) for child in raw_children]
    return VfsNode(name, NODE_TYPE_DIR, children=children)


def compute_sha256(raw_bytes):
    return hashlib.sha256(raw_bytes).hexdigest()


def load_vfs(vfs_path):
    with open(vfs_path, "rb") as vfs_file:
        raw_bytes = vfs_file.read()

    file_hash = compute_sha256(raw_bytes)

    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Некорректный JSON в файле VFS: {error}") from error

    vfs_name = data.get("name", DEFAULT_VFS_DISPLAY_NAME)
    root_raw = {
        "name": vfs_name,
        "type": NODE_TYPE_DIR,
        "children": data.get("children", []),
    }
    root_node = _build_node(root_raw)
    return root_node, vfs_name, file_hash
