import tkinter as tk
from tkinter import scrolledtext

VFS_NAME = "VFS"
PROMPT = "$ "
COMMANDS = ("ls", "cd")
EXIT_COMMAND = "exit"


def parse_input(raw_line):
    tokens = raw_line.split()
    if not tokens:
        return "", []
    return tokens[0], tokens[1:]


class EmulatorApp:

    def __init__(self, root, vfs_name=VFS_NAME):
        self.root = root
        self.vfs_name = vfs_name
        self._configure_window()
        self._build_input_output()
        self._print_welcome()

    def _configure_window(self):
        self.root.title(f"Эмулятор - [{self.vfs_name}]")
        self.root.geometry("800x500")

    def _build_input_output(self):
        self.output_area = scrolledtext.ScrolledText(self.root, state="disabled", wrap="word", bg="black", fg="white")
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

    def write_output(self, text):
        if not text.endswith("\n"):
            text += "\n"
        self.output_area.configure(state="normal")
        self.output_area.insert(tk.END, text)
        self.output_area.configure(state="disabled")
        self.output_area.see(tk.END)

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


def main():
    root = tk.Tk()
    EmulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()