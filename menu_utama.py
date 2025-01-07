import tkinter as tk
import subprocess
import os
from database import create_database

# Buat tabel-tabel yang dibutuhkan sebelum menjalankan aplikasi
create_database()

class MenuUtama:
    def __init__(self, root):
        self.root = root
        self.root.title("Menu Utama")
        self.app_input_process = None
        self.app_filter_process = None
        self.app_lihat_log_process = None
        self.app_master_supplier_process = None
        self.app_penerimaan_barang_process = None

        tk.Button(self.root, text="Aplikasi Input Produk", command=self.buka_app_input, width=25).pack(pady=20)
        tk.Button(self.root, text="Aplikasi Filter dan Edit", command=self.buka_app_filter, width=25).pack(pady=20)
        tk.Button(self.root, text="Lihat Catatan Log Produk", command=self.buka_app_lihat_log, width=25).pack(pady=20)
        tk.Button(self.root, text="Master Supplier", command=self.buka_app_master_supplier, width=25).pack(pady=20)
        tk.Button(self.root, text="Surat Penerimaan Barang", command=self.buka_app_penerimaan_barang, width=25).pack(pady=20)

    def buka_app_input(self):
        self.tutup_app_lainnya(self.app_input_process)
        if self.app_input_process is None or self.app_input_process.poll() is not None:
            self.app_input_process = subprocess.Popen(["python", "app_input_produk.py"])

    def buka_app_filter(self):
        self.tutup_app_lainnya(self.app_filter_process)
        if self.app_filter_process is None or self.app_filter_process.poll() is not None:
            self.app_filter_process = subprocess.Popen(["python", "app_filter_edit.py"])

    def buka_app_lihat_log(self):
        self.tutup_app_lainnya(self.app_lihat_log_process)
        if self.app_lihat_log_process is None or self.app_lihat_log_process.poll() is not None:
            self.app_lihat_log_process = subprocess.Popen(["python", "app_lihat_log.py"])

    def buka_app_master_supplier(self):
        self.tutup_app_lainnya(self.app_master_supplier_process)
        if self.app_master_supplier_process is None or self.app_master_supplier_process.poll() is not None:
            self.app_master_supplier_process = subprocess.Popen(["python", "app_master_supplier.py"])

    def buka_app_penerimaan_barang(self):
        # Tutup aplikasi lain jika sedang berjalan
        self.tutup_app_lainnya(self.app_penerimaan_barang_process)

        # Cek apakah aplikasi penerimaan barang sudah berjalan
        if self.app_penerimaan_barang_process is None or self.app_penerimaan_barang_process.poll() is not None:
            try:
                self.app_penerimaan_barang_process = subprocess.Popen(["python", "app_penerimaan_barang.py"])
            except Exception as e:
                print(f"Error saat membuka aplikasi penerimaan barang: {e}")

    def tutup_app_lainnya(self, current_process):
        processes = [self.app_input_process, self.app_filter_process, self.app_lihat_log_process, self.app_master_supplier_process, self.app_penerimaan_barang_process]
        for process in processes:
            if process is not None and process != current_process:
                self.tutup_app(process)

    def tutup_app(self, process):
        try:
            process.terminate()
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    root = tk.Tk()
    menu = MenuUtama(root)
    root.mainloop()