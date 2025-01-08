import tkinter as tk
from tkinter import ttk, messagebox
from produk_db import tambah_produk, ambil_semua_produk, ambil_produk_berdasarkan_nama_dan_varian
import random
import sqlite3

class AplikasiInputProduk:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Input Produk")

        # Variabel Form 1
        self.nama_produk = tk.StringVar()
        self.deskripsi = tk.StringVar()
        self.kode_toko_options = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        self.kode_toko = tk.StringVar(value=self.kode_toko_options[0])

        # Variabel Form 2
        self.nama_varian = tk.StringVar()

        # List untuk menyimpan data produk sementara
        self.data_produk_temp = []

        # Frame utama
        self.frame_utama = tk.Frame(self.root)
        self.frame_utama.pack(padx=10, pady=10)

        # Membuat Form 1 dan Form 2
        self.buat_form_input()
        self.buat_form_varian()

        # Tombol Tambah Varian
        self.btn_tambah_varian = tk.Button(self.frame_utama, text="Tambah Varian", command=self.tambah_varian)
        self.btn_tambah_varian.grid(row=6, column=0, columnspan=2, pady=5)

        # Tombol Posting
        self.btn_posting = tk.Button(self.frame_utama, text="Posting ke Database", command=self.posting_data)
        self.btn_posting.grid(row=7, column=0, columnspan=2, pady=5)

        # Frame Tabel
        self.frame_tabel = tk.Frame(self.root)
        self.frame_tabel.pack(padx=10, pady=10, fill="both", expand=True)

        # Membuat Tabel
        self.buat_tabel()

    def buat_form_input(self):
        # Form 1: Input Nama Produk, Deskripsi, Kode Toko
        frame_form1 = tk.LabelFrame(self.frame_utama, text="Informasi Produk")
        frame_form1.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        tk.Label(frame_form1, text="Nama Produk:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(frame_form1, textvariable=self.nama_produk).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_form1, text="Deskripsi:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(frame_form1, textvariable=self.deskripsi).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame_form1, text="Kode Toko:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        tk.OptionMenu(frame_form1, self.kode_toko, *self.kode_toko_options).grid(row=2, column=1, padx=5, pady=5, sticky="w")

    def buat_form_varian(self):
        # Form 2: Input Varian Warna
        frame_form2 = tk.LabelFrame(self.frame_utama, text="Varian Warna")
        frame_form2.grid(row=5, column=0, padx=5, pady=5, sticky="nsew")

        tk.Label(frame_form2, text="Nama Varian:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(frame_form2, textvariable=self.nama_varian).grid(row=0, column=1, padx=5, pady=5)

    def tambah_varian(self):
        nama_produk = self.nama_produk.get()
        deskripsi = self.deskripsi.get()
        kode_toko = self.kode_toko.get()
        nama_varian = self.nama_varian.get()

        # Validasi input
        if not nama_produk or not deskripsi or not kode_toko or not nama_varian:
            messagebox.showerror("Error", "Semua field harus diisi!")
            return

        # Cek apakah produk dengan nama dan varian yang sama sudah ada
        existing_product = ambil_produk_berdasarkan_nama_dan_varian(nama_produk, nama_varian)
        if existing_product:
            messagebox.showerror("Error", "Produk dengan nama dan varian yang sama sudah ada!")
            return

        # Cek apakah produk dengan nama yang sama sudah ada di data_produk_temp
        existing_kode_produk = None
        for item in self.data_produk_temp:
            if item[1] == nama_produk:
                existing_kode_produk = item[0]
                break

        # Jika produk dengan nama yang sama belum ada, cek di database
        if existing_kode_produk is None:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()
            cursor.execute("SELECT kode_produk FROM produk WHERE nama_produk = ? LIMIT 1", (nama_produk,))
            result = cursor.fetchone()
            conn.close()
            if result:
                existing_kode_produk = result[0]

        # Generate kode_produk (jika belum ada)
        if existing_kode_produk is None:
            kode_produk = self.generate_kode_produk(nama_produk)
        else:
            kode_produk = existing_kode_produk

        # Generate barcode dan kode_varian
        barcode = self.generate_barcode(kode_toko, kode_produk)
        kode_varian = barcode[-4:]

        # Tambah data ke list sementara
        self.data_produk_temp.append([kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian])

        # Update tabel
        self.update_tabel()

        # Reset input varian
        self.nama_varian.set("")

    def posting_data(self):
        if not self.data_produk_temp:
            messagebox.showwarning("Warning", "Tidak ada data untuk diposting!")
            return

        try:
            for data in self.data_produk_temp:
                tambah_produk(*data)
            messagebox.showinfo("Info", "Data berhasil diposting ke database!")
            
            # Clear input fields and temporary table after successful posting
            self.clear_form_and_table()
            
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat posting data: {e}")

    def buat_tabel(self):
        # Tabel untuk menampilkan data produk
        self.tabel = ttk.Treeview(self.frame_tabel, columns=("kode_produk", "nama_produk", "deskripsi", "kode_toko", "barcode", "kode_varian", "nama_varian"), show="headings")
        self.tabel.pack(fill="both", expand=True)

        # Define column headings
        self.tabel.heading("kode_produk", text="Kode Produk")
        self.tabel.heading("nama_produk", text="Nama Produk")
        self.tabel.heading("deskripsi", text="Deskripsi")
        self.tabel.heading("kode_toko", text="Kode Toko")
        self.tabel.heading("barcode", text="Barcode")
        self.tabel.heading("kode_varian", text="Kode Varian")
        self.tabel.heading("nama_varian", text="Nama Varian")

        # Set column widths
        self.tabel.column("kode_produk", width=100)
        self.tabel.column("nama_produk", width=150)
        self.tabel.column("deskripsi", width=200)
        self.tabel.column("kode_toko", width=50)
        self.tabel.column("barcode", width=100)
        self.tabel.column("kode_varian", width=100)
        self.tabel.column("nama_varian", width=100)

        # Add a vertical scrollbar
        yscrollbar = ttk.Scrollbar(self.frame_tabel, orient="vertical", command=self.tabel.yview)
        yscrollbar.pack(side="right", fill="y")
        self.tabel.configure(yscrollcommand=yscrollbar.set)

        self.update_tabel()

    def update_tabel(self):
        # Menghapus data lama di tabel
        for row in self.tabel.get_children():
            self.tabel.delete(row)

        # Menampilkan data dari list sementara (sesi ini saja)
        for data in self.data_produk_temp:
            self.tabel.insert("", tk.END, values=data)

        # Hapus kode yang menampilkan data dari database (baris di bawah ini dihapus)
        # data_db = ambil_semua_produk()
        # for data in data_db:
        #     self.tabel.insert("", tk.END, values=data)

    def generate_kode_produk(self, nama_produk):
        """Membuat kode produk 5 digit (huruf/angka)."""
        while True:
            # Generate 5 random alphanumeric characters
            random_chars = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5))
            kode_produk = random_chars
            return kode_produk
    
    def generate_barcode(self, kode_toko, kode_produk):
        """Membuat barcode 10 digit: [kode_toko][kode_produk 5 digit][kode_varian 4 digit]."""
        while True:
            kode_varian = ''.join(random.choices('0123456789', k=4))
            barcode = kode_toko + kode_produk + kode_varian

            # Check if the generated barcode already exists in the database
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM produk WHERE barcode = ?", (barcode,))
            count = cursor.fetchone()[0]
            conn.close()

            if count == 0:
                return barcode
    
    def clear_form_and_table(self):
        """Membersihkan input form dan tabel sementara."""
        self.nama_produk.set("")
        self.deskripsi.set("")
        self.kode_toko.set(self.kode_toko_options[0])
        self.nama_varian.set("")

        # Clear temporary data list
        self.data_produk_temp = []

        # Clear the table
        for row in self.tabel.get_children():
            self.tabel.delete(row)

if __name__ == "__main__":
    root = tk.Tk()
    aplikasi = AplikasiInputProduk(root)
    root.mainloop()