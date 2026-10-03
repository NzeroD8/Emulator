import argparse
import os
import time
import tkinter as tk
from tkinter import scrolledtext
from vfs import load_vfs

VFS_NAME = "VFS"
PROMPT = "$ "
EXIT_COMMAND = "exit"
LS_COMMAND = "ls"
CD_COMMAND = "cd"
PWD_COMMAND = "pwd"
TREE_COMMAND = "tree"
UPTIME_COMMAND = "uptime"
VFS_INFO_COMMAND = "vfs-info"
CHOWN_COMMAND = "chown"
RM_COMMAND = "rm"
COMMENT_PREFIX = "#"
TREE_INDENT = "  "


def parse_input(raw_line):
    tokens = raw_line.split()
    if not tokens:
        return "", []
    return tokens[0], tokens[1:]


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Графический эмулятор командной строки UNIX-подобной ОС."
    )
    parser.add_argument(
        "--vfs-path",
        dest="vfs_path",
        default=None,
        help="Путь к физическому расположению VFS.",
    )
    parser.add_argument(
        "--script",
        dest="script_path",
        default=None,
        help="Путь к стартовому скрипту с командами эмулятора.",
    )
    return parser


def parse_em_args(argv=None):
    parser = build_arg_parser()
    return parser.parse_args(argv)


def define_vfs_name(vfs_path):
    if not vfs_path:
        return VFS_NAME
    file_name = os.path.basename(vfs_path)
    name_without_ext, _ = os.path.splitext(file_name)
    return name_without_ext or VFS_NAME


def read_script_lines(script_path):
    with open(script_path, "r", encoding="utf-8") as script_file:
        raw_lines = script_file.readlines()
    return [
        line.strip()
        for line in raw_lines
        if line.strip() and not line.strip().startswith(COMMENT_PREFIX)
    ]


def split_path_segments(path_str):
    return [
        segment
        for segment in path_str.strip("/").split("/")
        if segment and segment != "."
    ]


class EmulatorApp:

    def __init__(self, root, vfs_name=VFS_NAME, vfs_path=None,
                 script_path=None):
        self.start_time = time.monotonic()
        self.root = root
        self.vfs_name = vfs_name
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.vfs_root = None
        self.vfs_hash = None
        self.dir_stack = None
        self._configure_window()
        self._build_input_output()
        self._print_welcome()
        self._print_debug_parameters()
        if self.vfs_path:
            self._load_vfs()
        if self.script_path:
            self.root.after(0, self.run_starting_script, self.script_path)

    def _configure_window(self):
        self.root.title(f"Эмулятор - [{self.vfs_name}]")
        self.root.geometry("800x500")

    def _build_input_output(self):
        self.output_area = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap="word", bg="black", fg="white"
        )
        self.output_area.pack(expand=True, fill="both", padx=5, pady=5)

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill="x", padx=5, pady=5)

        self.prompt_label = tk.Label(input_frame, text=PROMPT)
        self.prompt_label.pack(side="left")

        self.input_entry = tk.Entry(input_frame)
        self.input_entry.pack(side="left", expand=True, fill="x")
        self.input_entry.bind("<Return>", self._enter_pressed)
        self.input_entry.focus_set()

    def _print_welcome(self):
        self.write_output(
            "Эмулятор командной строки. Введите 'exit' для выхода.\n"
        )

    def _print_debug_parameters(self):
        self.write_output("Отладочный вывод параметров запуска:")
        self.write_output(f"  Путь к VFS: {self.vfs_path or '(не задан)'}")
        self.write_output(
            f"  Путь к стартовому скрипту: "
            f"{self.script_path or '(не задан)'}"
        )

    def _load_vfs(self):
        try:
            loaded_root, loaded_name, loaded_hash = load_vfs(self.vfs_path)
        except (OSError, ValueError) as error:
            self.write_output(f"Ошибка загрузки VFS: {error}")
            return
        self.vfs_root = loaded_root
        self.vfs_hash = loaded_hash
        self.vfs_name = loaded_name
        self.dir_stack = [self.vfs_root]
        self.root.title(f"Эмулятор - [{self.vfs_name}]")
        self.write_output(f"VFS '{self.vfs_name}' успешно загружена.")

    def write_output(self, text):
        if not text.endswith("\n"):
            text += "\n"
        self.output_area.configure(state="normal")
        self.output_area.insert(tk.END, text)
        self.output_area.configure(state="disabled")
        self.output_area.see(tk.END)

    def run_starting_script(self, script_path):
        try:
            commands = read_script_lines(script_path)
        except OSError as error:
            self.write_output(f"Ошибка запуска скрипта: {error}")
            return
        for command_line in commands:
            self.write_output(f"{PROMPT}{command_line}")
            self.execute_line(command_line)

    def _enter_pressed(self, event):
        raw_line = self.input_entry.get()
        self.input_entry.delete(0, tk.END)
        self.write_output(f"{PROMPT}{raw_line}")
        self.execute_line(raw_line)

    def execute_line(self, raw_line):
        command, args = parse_input(raw_line)
        if not command:
            return
        if command == EXIT_COMMAND:
            self.root.quit()
            return
        try:
            self._dispatch_command(command, args)
        except Exception as error:
            self.write_output(
                f"Ошибка выполнения команды '{command}': {error}"
            )

    def _dispatch_command(self, command, args):
        if command == VFS_INFO_COMMAND:
            self.write_output(self._format_vfs_info())
            return
        if command == LS_COMMAND:
            self._cmd_ls(args)
            return
        if command == CD_COMMAND:
            self._cmd_cd(args)
            return
        if command == PWD_COMMAND:
            self._cmd_pwd()
            return
        if command == TREE_COMMAND:
            self._cmd_tree()
            return
        if command == UPTIME_COMMAND:
            self._cmd_uptime()
            return
        if command == CHOWN_COMMAND:
            self._cmd_chown(args)
            return
        if command == RM_COMMAND:
            self._cmd_rm(args)
            return
        self.write_output(f"Ошибка: неизвестная команда '{command}'")

    def _format_vfs_info(self):
        if self.vfs_root is None:
            return "Ошибка: VFS не загружена"
        return f"Имя VFS: {self.vfs_name}\nSHA-256: {self.vfs_hash}"

    def _resolve_node(self, path_str):
        segments = split_path_segments(path_str)
        stack = [self.vfs_root] if path_str.startswith("/") else list(self.dir_stack)
        node = stack[-1]
        for index, segment in enumerate(segments):
            if segment == "..":
                if len(stack) > 1:
                    stack.pop()
                node = stack[-1]
                continue
            child = node.find_child(segment)
            if child is None:
                raise ValueError(f"нет такого файла или директории: {segment}")
            is_last = index == len(segments) - 1
            if not is_last and not child.is_dir():
                raise ValueError(f"не является директорией: {segment}")
            node = child
            if child.is_dir():
                stack.append(child)
        return node, stack

    def _resolve_parent_and_child(self, path_str):
        segments = split_path_segments(path_str)
        if not segments:
            raise ValueError("нужно указать имя файла или директории")
        if segments[-1] == "..":
            raise ValueError("нельзя применить команду к '..'")
        stack = [self.vfs_root] if path_str.startswith("/") else list(self.dir_stack)
        node = stack[-1]
        for segment in segments[:-1]:
            if segment == "..":
                if len(stack) > 1:
                    stack.pop()
                node = stack[-1]
                continue
            child = node.find_child(segment)
            if child is None or not child.is_dir():
                raise ValueError(f"нет такой директории: {segment}")
            node = child
            stack.append(child)
        target_name = segments[-1]
        target = node.find_child(target_name)
        if target is None:
            raise ValueError(f"нет такого файла или директории: {target_name}")
        return node, target

    def _cmd_ls(self, args):
        if not self.dir_stack:
            self.write_output("Ошибка: VFS не загружена")
            return
        target = self.dir_stack[-1]
        if args:
            try:
                target, _ = self._resolve_node(args[0])
            except ValueError as error:
                self.write_output(f"ls: {error}")
                return
        if target.is_file():
            self.write_output(target.name)
            return
        self.write_output(self._format_listing(target))

    def _format_listing(self, dir_node):
        if not dir_node.children:
            return "(пусто)"
        names = sorted(dir_node.children, key=lambda node: node.name)
        labels = [f"{n.name}/" if n.is_dir() else n.name for n in names]
        return "  ".join(labels)

    def _cmd_cd(self, args):
        if not self.dir_stack:
            self.write_output("Ошибка: VFS не загружена")
            return
        if not args:
            self.dir_stack = [self.vfs_root]
            return
        try:
            target, stack = self._resolve_node(args[0])
        except ValueError as error:
            self.write_output(f"cd: {error}")
            return
        if not target.is_dir():
            self.write_output(f"cd: не является директорией: {args[0]}")
            return
        self.dir_stack = stack

    def _cmd_pwd(self):
        if not self.dir_stack:
            self.write_output("Ошибка: VFS не загружена")
            return
        self.write_output(self._current_path_string())

    def _current_path_string(self):
        names = [node.name for node in self.dir_stack[1:]]
        return "/" + "/".join(names)

    def _cmd_tree(self):
        if not self.dir_stack:
            self.write_output("Ошибка: VFS не загружена")
            return
        lines = []
        self._collect_tree_lines(self.dir_stack[-1], 0, lines)
        self.write_output("\n".join(lines))

    def _collect_tree_lines(self, node, depth, lines):
        indent = TREE_INDENT * depth
        label = f"{node.name}/" if node.is_dir() else node.name
        lines.append(f"{indent}{label}")
        for child in sorted(node.children, key=lambda item: item.name):
            self._collect_tree_lines(child, depth + 1, lines)

    def _cmd_uptime(self):
        elapsed_seconds = time.monotonic() - self.start_time
        self.write_output(f"uptime: {elapsed_seconds:.1f} сек")

    def _cmd_chown(self, args):
        if not self.dir_stack:
            self.write_output("Ошибка: VFS не загружена")
            return
        if len(args) != 2:
            self.write_output("chown: использование: chown <путь> <владелец>")
            return
        path_str, new_owner = args
        try:
            _, target = self._resolve_parent_and_child(path_str)
        except ValueError as error:
            self.write_output(f"chown: {error}")
            return
        target.owner = new_owner
        self.write_output(f"chown: {path_str} -> {new_owner}")

    def _cmd_rm(self, args):
        if not self.dir_stack:
            self.write_output("Ошибка: VFS не загружена")
            return
        if not args:
            self.write_output("rm: укажите путь к файлу или директории")
            return
        path_str = args[0]
        try:
            parent, target = self._resolve_parent_and_child(path_str)
        except ValueError as error:
            self.write_output(f"rm: {error}")
            return
        parent.children.remove(target)
        self.write_output(f"rm: удалён {path_str}")


def main(argv=None):
    args = parse_em_args(argv)
    vfs_name = define_vfs_name(args.vfs_path)
    root = tk.Tk()
    EmulatorApp(
        root,
        vfs_name=vfs_name,
        vfs_path=args.vfs_path,
        script_path=args.script_path,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
