import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class WindowLihatStok:
    def __init__(self, root):
        self.root = root
        self.root.title("Lihat Stok")
        self.root.geometry("800x600")

        # --- Variabel ---
        self.current_page = 1
        self.data_per_page = 20
        self.total_data = 0

        self.search_barcode = tk.StringVar()
        self.search_nama_produk = tk.StringVar()
        self.filter_toko = tk.StringVar(value="Semua")
        self.sort_by = tk.StringVar(value="stok_terbanyak")

        # --- Frame Pencarian ---
        frame_pencarian = tk.LabelFrame(self.root, text="Pencarian")
        frame_pencarian.pack(padx=10, pady=10, fill="x")

        tk.Label(frame_pencarian, text="Barcode:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(frame_pencarian, textvariable=self.search_barcode).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(frame_pencarian, text="Nama Produk:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        tk.Entry(frame_pencarian, textvariable=self.search_nama_produk).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        tk.Button(frame_pencarian, text="Cari", command=self.cari_data).grid(row=0, column=4, padx=5, pady=5)
        tk.Button(frame_pencarian, text="Clear", command=self.clear_search).grid(row=0, column=5, padx=5, pady=5)

        # --- Frame Filter ---
        frame_filter = tk.LabelFrame(self.root, text="Filter")
        frame_filter.pack(padx=10, pady=5, fill="x")

        tk.Label(frame_filter, text="Toko:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.toko_options = ["Semua", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        tk.OptionMenu(frame_filter, self.filter_toko, *self.toko_options, command=self.filter_data).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- Frame Sorting ---
        frame_sort = tk.LabelFrame(self.root, text="Urutkan")
        frame_sort.pack(padx=10, pady=5, fill="x")

        tk.Radiobutton(frame_sort, text="Stok Terbanyak", variable=self.sort_by, value="stok_terbanyak", command=self.refresh_data).pack(side="left", padx=5)
        tk.Radiobutton(frame_sort, text="Stok Paling Sedikit", variable=self.sort_by, value="stok_tersedikit", command=self.refresh_data).pack(side="left", padx=5)

        # --- Tabel ---
        self.frame_tabel = tk.Frame(self.root)
        self.frame_tabel.pack(padx=10, pady=5, fill="both", expand=True)
        self.buat_tabel()

        # --- Pagination ---
        self.frame_pagination = tk.Frame(self.root)
        self.frame_pagination.pack(padx=10, pady=5, fill="x")

        self.btn_prev = tk.Button(self.frame_pagination, text="<< Prev", command=self.prev_page, state="disabled")
        self.btn_prev.pack(side="left", padx=5)

        self.label_page = tk.Label(self.frame_pagination, text=f"Halaman {self.current_page} dari {self.total_pages()}")
        self.label_page.pack(side="left", padx=5)

        self.btn_next = tk.Button(self.frame_pagination, text="Next >>", command=self.next_page)
        self.btn_next.pack(side="left", padx=5)

        # --- Status Bar ---
        self.status_bar = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Load Data Awal ---
        self.refresh_data()

    def buat_tabel(self):
        """Membuat tabel untuk menampilkan data stok."""
        self.tabel = ttk.Treeview(self.frame_tabel, columns=("barcode", "nama_produk", "varian", "kode_toko", "stok"), show="headings")
        self.tabel.pack(fill="both", expand=True)

        self.tabel.heading("barcode", text="Barcode")
        self.tabel.heading("nama_produk", text="Nama Produk")
        self.tabel.heading("varian", text="Varian")
        self.tabel.heading("kode_toko", text="Kode Toko")
        self.tabel.heading("stok", text="Stok")

        self.tabel.column("barcode", width=150)
        self.tabel.column("nama_produk", width=200)
        self.tabel.column("varian", width=150)
        self.tabel.column("kode_toko", width=50)
        self.tabel.column("stok", width=50)

        yscrollbar = ttk.Scrollbar(self.frame_tabel, orient="vertical", command=self.tabel.yview)
        yscrollbar.pack(side="right", fill="y")
        self.tabel.configure(yscrollcommand=yscrollbar.set)

    def refresh_data(self):
        """Mengambil data stok dari database dan memperbarui tabel."""
        conn = None
        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()

            # Filter dan Cari
            query = "SELECT p.barcode, p.nama_produk, p.nama_varian, p.kode_toko, s.qty_stok FROM stok s JOIN produk p ON s.barcode = p.barcode WHERE 1=1"
            params = []

            if self.search_barcode.get():
                query += " AND p.barcode LIKE ?"
                params.append(f"%{self.search_barcode.get()}%")
            if self.search_nama_produk.get():
                query += " AND p.nama_produk LIKE ?"
                params.append(f"%{self.search_nama_produk.get()}%")
            if self.filter_toko.get() != "Semua":
                query += " AND p.kode_toko = ?"
                params.append(self.filter_toko.get())

            # Sorting
            if self.sort_by.get() == "stok_terbanyak":
                query += " ORDER BY s.qty_stok DESC"
            elif self.sort_by.get() == "stok_tersedikit":
                query += " ORDER BY s.qty_stok ASC"

            # Pagination
            cursor.execute(query, params)
            self.total_data = len(cursor.fetchall())  # Hitung total data setelah filter dan pencarian
            query += " LIMIT ?, ?"
            params.extend([(self.current_page - 1) * self.data_per_page, self.data_per_page])

            cursor.execute(query, params)
            data_stok = cursor.fetchall()

            # Update Tabel
            for row in self.tabel.get_children():
                self.tabel.delete(row)
            for data in data_stok:
                self.tabel.insert("", tk.END, values=data)

            # Update Status Bar
            self.update_status_bar()

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        finally:
            if conn:
                conn.close()

        self.update_pagination_buttons()

    def cari_data(self):
        """Memulai pencarian data berdasarkan barcode atau nama produk."""
        self.current_page = 1
        self.refresh_data()

    def clear_search(self):
        """Membersihkan field pencarian."""
        self.search_barcode.set("")
        self.search_nama_produk.set("")
        self.current_page = 1  # Reset paginasi
        self.refresh_data()

    def filter_data(self, *args):
        """Memfilter data berdasarkan toko."""
        self.current_page = 1
        self.refresh_data()

    def update_status_bar(self):
        """Memperbarui teks pada status bar."""
        conn = None
        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()

            # Hitung jumlah produk dan total stok
            cursor.execute("SELECT COUNT(DISTINCT barcode), SUM(qty_stok) FROM stok")
            result = cursor.fetchone()
            jumlah_produk = result[0] if result[0] else 0
            total_stok = result[1] if result[1] else 0

            self.status_bar.config(text=f"Jumlah Produk: {jumlah_produk} | Total Stok: {total_stok}")

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        finally:
            if conn:
                conn.close()

    def total_pages(self):
        """Menghitung total halaman."""
        return (self.total_data + self.data_per_page - 1) // self.data_per_page

    def next_page(self):
        """Menampilkan halaman berikutnya."""
        if self.current_page < self.total_pages():
            self.current_page += 1
            self.refresh_data()

    def prev_page(self):
        """Menampilkan halaman sebelumnya."""
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_data()

    def update_pagination_buttons(self):
        """Mengaktifkan/menonaktifkan tombol navigasi halaman."""
        total_pages = self.total_pages()
        self.label_page.config(text=f"Halaman {self.current_page} dari {total_pages}")

        if self.current_page == 1:
            self.btn_prev.config(state="disabled")
        else:
            self.btn_prev.config(state="normal")

        if self.current_page == total_pages or total_pages == 0:
            self.btn_next.config(state="disabled")
        else:
            self.btn_next.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    aplikasi = WindowLihatStok(root)
    root.mainloop()