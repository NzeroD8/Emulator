import argparse
import os
import tkinter as tk
from tkinter import scrolledtext

VFS_NAME = "VFS"
PROMPT = "$ "
COMMANDS = ("ls", "cd")
EXIT_COMMAND = "exit"
COMMENT_PREFIX = "#"


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

class EmulatorApp:

    def __init__(self, root, vfs_name=VFS_NAME, vfs_path=None,
                 script_path=None):
        self.root = root
        self.vfs_name = vfs_name
        self.vfs_path = vfs_path
        self.script_path = script_path
        self._configure_window()
        self._build_input_output()
        self._print_welcome()
        self._print_debug_parameters()
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
        self.write_output("Эмулятор командной строки. Введите 'exit' для выхода.\n")

    def _print_debug_parameters(self):
        self.write_output("Отладочный вывод параметров запуска:")
        self.write_output(f"  Путь к VFS: {self.vfs_path or '(не задан)'}")
        self.write_output(
            f"  Путь к стартовому скрипту: "
            f"{self.script_path or '(не задан)'}"
        )

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
        if command in COMMANDS:
            self.write_output(self._format_output(command, args))
            return
        self.write_output(f"Ошибка: неизвестная команда '{command}'")

    def _format_output(self, command, args):
        if args:
            return f"{command}: {' '.join(args)}"
        return f"{command}: (без аргументов)"


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
