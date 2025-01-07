import tkinter as tk
from tkinter import ttk
import sqlite3

class WindowLihatLog:
    def __init__(self, root):
        self.root = root
        self.root.title("Lihat Catatan Log Produk")

        # --- Frame ---
        self.frame_log = tk.Frame(self.root)
        self.frame_log.pack(padx=10, pady=10, fill="both", expand=True)
        self.buat_log_view()

    def buat_log_view(self):
        """Membuat tampilan log."""
        self.log_view = tk.Text(self.frame_log, wrap=tk.WORD)
        self.log_view.pack(fill="both", expand=True)

        # Add a vertical scrollbar
        yscrollbar = ttk.Scrollbar(self.frame_log, orient="vertical", command=self.log_view.yview)
        yscrollbar.pack(side="right", fill="y")
        self.log_view.configure(yscrollcommand=yscrollbar.set)

        self.log_view.config(state="disabled")  # Disable editing

        self.refresh_data()

    def refresh_data(self):
        """Mengambil data log dari database dan memperbarui tampilan."""
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log_produk ORDER BY waktu DESC")  # Urutkan berdasarkan waktu secara descending
        data_log = cursor.fetchall()
        conn.close()

        self.log_view.config(state="normal")  # Enable editing temporarily
        self.log_view.delete(1.0, tk.END)  # Clear existing content

        for data in data_log:
            kalimat_log = self.format_log_entry(data)
            self.log_view.insert(tk.END, kalimat_log + "\n\n")

        self.log_view.config(state="disabled")  # Disable editing again

    def format_log_entry(self, data):
        """Memformat data log menjadi kalimat."""
        id_log, aksi, waktu, data_lama, data_baru, keterangan = data

        kalimat = f"ID Log: {id_log}\n"
        kalimat += f"Aksi: {aksi}\n"
        kalimat += f"Waktu: {waktu}\n"

        if data_lama != "None":
            kalimat += f"Data Lama: {data_lama}\n"
        if data_baru != "None":
            kalimat += f"Data Baru: {data_baru}\n"

        kalimat += f"Keterangan: {keterangan}\n"

        return kalimat

if __name__ == "__main__":
    root = tk.Tk()
    aplikasi = WindowLihatLog(root)
    root.mainloop()