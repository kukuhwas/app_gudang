import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sqlite3
import random
from produk_db import tambah_produk, ambil_produk_berdasarkan_nama_dan_varian, catat_log

class ImportProdukWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Import Data Produk")

        self.file_path = tk.StringVar()
        self.log_text = tk.StringVar()

        # Instruksi untuk user
        instruksi = """
        Format File CSV:
        - Header wajib: kode_produk;nama_produk;kode_toko;nama_varian
        - Kolom opsional: deskripsi;barcode;kode_varian
        - Delimiter: ';' (titik koma)
        - Barcode akan di-generate otomatis jika dikosongkan.
        - Kode varian akan di-generate otomatis jika kosong berdasarkan 4 digit terakhir barcode.
        - Pastikan tidak ada data produk dengan nama dan varian yang sama di dalam database.

        Contoh Isi File CSV:
        kode_produk;nama_produk;deskripsi;kode_toko;barcode;kode_varian;nama_varian
        P0001;Gamis Katun Madina;Gamis bahan katun Madina, polos, adem, dan nyaman dipakai;1;;;Biru Dongker
        P0002;Khimar Ceruti Babydoll;Khimar bahan ceruti babydoll, dua layer, pet antem;2;B000212345;V001;Hitam
        """

        # Label Instruksi
        ttk.Label(self.root, text=instruksi, justify="left", wraplength=450).grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        # Separator
        ttk.Separator(self.root, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        # Label dan Entry untuk menampilkan path file
        ttk.Label(self.root, text="File:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.root, textvariable=self.file_path, state="readonly", width=50).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(self.root, text="Browse", command=self.browse_file).grid(row=2, column=2, padx=5, pady=5)

        # Tombol Import
        ttk.Button(self.root, text="Import", command=self.import_data).grid(row=3, column=0, columnspan=3, pady=10)

        # Text area untuk log
        self.log_area = tk.Text(self.root, wrap=tk.WORD, state="disabled")
        self.log_area.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # Konfigurasi grid
        self.root.grid_rowconfigure(4, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def browse_file(self):
        # Membuka dialog untuk memilih file
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if file_path:
            self.file_path.set(file_path)

    def import_data(self):
        # Logika untuk impor data
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showwarning("Peringatan", "Pilih file terlebih dahulu!")
            return

        try:
            # Baca file CSV atau Excel
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, delimiter=';') # Ubah delimiter jika perlu
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                messagebox.showerror("Error", "Format file tidak didukung!")
                return

            # Validasi Header
            expected_headers = ['kode_produk', 'nama_produk', 'kode_toko', 'nama_varian'] # Header yang wajib
            if not all(header in df.columns for header in expected_headers):
                missing_headers = [header for header in expected_headers if header not in df.columns]
                messagebox.showerror("Error", f"Header tidak sesuai! Header yang wajib ada: {', '.join(missing_headers)}")
                return

            # Proses data (validasi dan penyimpanan ke database)
            self.proses_data(df)

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat membaca file: {e}")

    def proses_data(self, df):
        conn = None  # Inisialisasi conn
        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()

            for index, row in df.iterrows():
                try:
                    # Required Fields
                    kode_produk = str(row['kode_produk'])
                    nama_produk = str(row['nama_produk'])
                    kode_toko = str(row['kode_toko'])
                    nama_varian = str(row['nama_varian'])

                    # Optional Fields
                    deskripsi = str(row['deskripsi']) if 'deskripsi' in row and pd.notna(row['deskripsi']) else ""
                    barcode = str(row['barcode']) if 'barcode' in row and pd.notna(row['barcode']) else None
                    kode_varian = str(row['kode_varian']) if 'kode_varian' in row and pd.notna(row['kode_varian']) else ""

                    # Validasi Required Fields
                    if not all([kode_produk, nama_produk, kode_toko, nama_varian]):
                        raise ValueError("Data tidak lengkap. Pastikan kolom kode_produk, nama_produk, kode_toko, dan nama_varian terisi.")

                    # Validasi Kode Toko
                    if kode_toko not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                        raise ValueError(f"Kode toko '{kode_toko}' tidak valid")

                    # Generate Barcode jika Kosong
                    if barcode is None or barcode.strip() == "":
                        barcode = self.generate_barcode(kode_toko, kode_produk)

                    # Generate atau Validasi Kode Varian
                    if not kode_varian:
                        # Cek apakah varian sudah ada untuk produk ini
                        cursor.execute("SELECT kode_varian FROM produk WHERE kode_produk = ? AND nama_varian = ?", (kode_produk, nama_varian))
                        existing_kode_varian = cursor.fetchone()
                        if existing_kode_varian:
                            kode_varian = existing_kode_varian[0]
                        else:
                            # Generate kode varian baru jika belum ada
                            kode_varian = self.generate_kode_varian(barcode)  # Anda perlu mendefinisikan fungsi ini
                    else:
                      # Validasi Keunikan Barcode jika diisi manual
                      cursor.execute("SELECT COUNT(*) FROM produk WHERE barcode = ?", (barcode,))
                      if cursor.fetchone()[0] > 0:
                          raise ValueError(f"Barcode {barcode} sudah ada di database")

                    # Cek apakah produk dengan nama dan varian yang sama sudah ada
                    existing_product = ambil_produk_berdasarkan_nama_dan_varian(nama_produk, nama_varian)
                    if existing_product:
                        raise ValueError(f"Produk dengan nama '{nama_produk}' dan varian '{nama_varian}' sudah ada")

                    # Tambahkan produk
                    tambah_produk(kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian)
                    self.update_log(f"Baris {index + 2}: Produk {nama_produk} varian {nama_varian} berhasil diimpor.")
                    catat_log('IMPORT PRODUK', None, str(row.to_dict()),'Produk berhasil diimpor')

                except ValueError as ve:
                    self.update_log(f"Baris {index + 2}: Gagal diimpor - {ve}")
                    catat_log('IMPORT PRODUK', None, str(row.to_dict()), f'Produk gagal diimpor - {ve}')
                except Exception as e:
                    self.update_log(f"Baris {index + 2}: Gagal diimpor - {e}")
                    catat_log('IMPORT PRODUK', None, str(row.to_dict()), f'Produk gagal diimpor - {e}')

            conn.commit()
            messagebox.showinfo("Info", "Impor data selesai!")

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat memproses data: {e}")
        finally:
            if conn:
                conn.close()

    def generate_kode_varian(self, barcode):
        """Membuat kode varian 4 digit dari 4 digit terakhir barcode."""
        if len(barcode) >= 4:
            return barcode[-4:]
        else:
            # Handle jika barcode kurang dari 4 digit (misalnya, generate random)
            return ''.join(random.choices('0123456789', k=4))

    def generate_barcode(self, kode_toko, kode_produk):
        """Membuat barcode 13 digit: [kode_toko 1 digit][kode_produk 5 digit][kode_varian 4 digit][random 3 digit]."""
        while True:
            random_part = ''.join(random.choices('0123456789', k=3))
            kode_varian_part = ''.join(random.choices('0123456789', k=4))
            barcode = kode_toko + kode_produk[-5:] + kode_varian_part + random_part

            # Cek keunikan barcode
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM produk WHERE barcode = ?", (barcode,))
            count = cursor.fetchone()[0]
            conn.close()

            if count == 0:
                return barcode

    def update_log(self, message):
        # Update log area
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.config(state="disabled")
        self.log_area.see(tk.END)  # Auto-scroll ke bawah

if __name__ == "__main__":
    root = tk.Tk()
    ImportProdukWindow(root)
    root.mainloop()