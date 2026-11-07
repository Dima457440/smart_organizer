import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from file_scanner import scan_files, find_duplicates
from hash_calculator import sha256_hash
from cleaner import safe_delete
from report_writer import write_report

logging.basicConfig(
    filename="errors.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Умный органайзер файлов")
        self.geometry("1200x650")
        self.duplicates = []
        self.zero_byte = []
        self.stats = {"total": 0, "hashed": 0}
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        self.folder_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.folder_var).pack(side="left", fill="x", expand=True)
        ttk.Button(top, text="Выбрать папку", command=self.choose_folder).pack(side="left", padx=4)
        ttk.Button(top, text="Сканировать", command=self.scan).pack(side="left")
        ttk.Button(top, text="Удалить выбранные", command=self.delete_selected).pack(side="left", padx=4)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

        cols = ("name", "path", "size", "hash")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")
        # Hash = 560px — полный SHA-256 (64 hex) легко читается
        widths = {"name": 180, "path": 340, "size": 90, "hash": 560}
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=widths[c], anchor="w")

        sy = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        sx = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=sy.set, xscroll=sx.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.status = tk.StringVar(value="Готово")
        ttk.Label(self, textvariable=self.status, relief="sunken").pack(fill="x")

    def choose_folder(self):
        self.folder_var.set(filedialog.askdirectory() or "")

    def scan(self):
        folder = self.folder_var.get()
        if not folder:
            messagebox.showwarning("Внимание", "Выберите папку")
            return
        self.tree.delete(*self.tree.get_children())
        self.status.set("Сканирование...")
        self.update_idletasks()

        files = scan_files(folder)
        self.duplicates, self.zero_byte, self.stats = find_duplicates(files, sha256_hash)

        import os
        for group in self.duplicates:
            for f in group:
                self.tree.insert("", "end", values=(os.path.basename(f["path"]),
                                                    f["path"], f["size"], f["hash"]))
        for f in self.zero_byte:
            self.tree.insert("", "end", values=(os.path.basename(f["path"]),
                                                f["path"], 0, "-"))

        access_errors = sum(1 for f in files if f.get("error"))
        self.status.set(
            f"Дубликатов: {len(self.duplicates)} групп, "
            f"пустых: {len(self.zero_byte)}, "
            f"Ошибок доступа: {access_errors}, "
            f"Хэшировано: {self.stats['hashed']} из {self.stats['total']}"
        )
        write_report("report.json", self.duplicates, self.zero_byte, files, self.stats)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        paths = [self.tree.item(i, "values")[1] for i in selected]
        if not messagebox.askyesno("Подтверждение", f"Удалить {len(paths)} файл(ов)?"):
            return
        deleted, failed, protected = safe_delete(paths, self.duplicates)
        for i in selected:
            if self.tree.item(i, "values")[1] in deleted:
                self.tree.delete(i)
        self.status.set(f"Удалено: {len(deleted)}, ошибок: {len(failed)}, "
                        f"защищено: {len(protected)}")
        if protected:
            messagebox.showinfo("Защита оригинала",
                                "Нельзя удалить все копии. Защищены:\n" + "\n".join(protected))
        if failed:
            messagebox.showwarning("Ошибки", "\n".join(p for p, _ in failed))


if __name__ == "__main__":
    App().mainloop()