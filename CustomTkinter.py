import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

class RenamerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Переименование чертежей GLE-RD")
        self.geometry("600x450")
        self.minsize(550, 400)

        # Default values
        self.path_var = tk.StringVar(value=r"C:\Users\i.danilov\Desktop\В работе\вахта 3\TQ-12523-00\03.Result")
        self.start_num_var = tk.StringVar(value="4")
        self.suffix_var = tk.StringVar(value="M")
        self.rev_var = tk.StringVar(value="04")
        self.chg_var = tk.StringVar(value="2")

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)

        # --- Path selection ---
        path_frame = ttk.LabelFrame(main_frame, text=" Директория с файлами ", padding="10")
        path_frame.pack(fill="x", pady=(0, 10))

        ttk.Entry(path_frame, textvariable=self.path_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(path_frame, text="Обзор...", command=self.browse_folder).pack(side="right")

        # --- Template parameters ---
        params_frame = ttk.LabelFrame(main_frame, text=" Настройки шаблона ", padding="10")
        params_frame.pack(fill="x", pady=(0, 10))

        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(3, weight=1)

        ttk.Label(params_frame, text="Начальный номер:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(params_frame, textvariable=self.start_num_var, width=10).grid(row=0, column=1, sticky="w", pady=5, padx=5)

        ttk.Label(params_frame, text="Буква индекса (M/М):").grid(row=0, column=2, sticky="w", pady=5, padx=5)
        ttk.Entry(params_frame, textvariable=self.suffix_var, width=10).grid(row=0, column=3, sticky="w", pady=5, padx=5)

        ttk.Label(params_frame, text="Ревизия (04):").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(params_frame, textvariable=self.rev_var, width=10).grid(row=1, column=1, sticky="w", pady=5, padx=5)

        ttk.Label(params_frame, text="Изменение (изм_...):").grid(row=1, column=2, sticky="w", pady=5, padx=5)
        ttk.Entry(params_frame, textvariable=self.chg_var, width=10).grid(row=1, column=3, sticky="w", pady=5, padx=5)

        # --- Run button ---
        self.btn_run = ttk.Button(main_frame, text="ЗАПУСТИТЬ ПЕРЕИМЕНОВАНИЕ", command=self.process_files)
        self.btn_run.pack(fill="x", pady=(0, 10))

        # --- Log area ---
        log_frame = ttk.LabelFrame(main_frame, text=" Журнал операций ", padding="5")
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, wrap="word", height=10, bg="#f8f9fa", state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orientation="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

    def browse_folder(self):
        selected_dir = filedialog.askdirectory(initialdir=self.path_var.get())
        if selected_dir:
            self.path_var.set(selected_dir)

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def process_files(self):
        self.clear_log()

        # --- Validate inputs ---
        target_dir = Path(self.path_var.get().strip())
        if not target_dir.exists() or not target_dir.is_dir():
            messagebox.showerror("Ошибка", f"Путь не найден или не является папкой:\n{target_dir}")
            return

        try:
            start_num = int(self.start_num_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Поле 'Начальный номер' должно содержать целое число!")
            return

        suffix = self.suffix_var.get().strip()
        rev = self.rev_var.get().strip()
        chg = self.chg_var.get().strip()

        if not suffix or not rev or not chg:
            messagebox.showerror("Ошибка", "Все поля параметров должны быть заполнены!")
            return

        # --- Find files ---
        # If you want ONLY latin 'P', change [PР] to P
        pattern = re.compile(r"^GLE-RD-\([PР]0-.+?\).*")
        files = [f for f in target_dir.iterdir() if f.is_file() and pattern.match(f.name)]
        files.sort(key=lambda x: x.name)

        if not files:
            self.log("Файлы с маской 'GLE-RD-(P0-...)' не найдены.")
            messagebox.showinfo("Готово", "Файлы для обработки не найдены.")
            return

        self.log(f"Найдено файлов: {len(files)}\n" + "-" * 50)

        success_count = 0
        for idx, file_path in enumerate(files):
            new_num = start_num + idx
            base_name = file_path.stem  # имя без расширения

            # Формируем новое имя (всегда с .pdf)
            new_name = f"{new_num}{suffix}. {base_name} (RU)_{rev}_изм_{chg}.pdf"
            new_path = target_dir / new_name

            try:
                file_path.rename(new_path)
                self.log(f"[OK] {file_path.name}  →  {new_name}")
                success_count += 1
            except Exception as e:
                self.log(f"[ERR] {file_path.name}: {e}")

        self.log("-" * 50)
        self.log(f"Готово. Переименовано: {success_count} из {len(files)}.")
        messagebox.showinfo("Успех", f"Переименовано файлов: {success_count}")

if __name__ == "__main__":
    app = RenamerApp()
    app.mainloop()