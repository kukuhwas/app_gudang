import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from difflib import SequenceMatcher
import random
from database import catat_log # Import fungsi catat_log

class WindowFilter:
    def __init__(self, root):
        self.root = root
        self.root.title("Filter dan Edit Data Produk")

        # --- Filtering ---
        self.filter_nama_produk = tk.StringVar()
        self.filter_nama_produk.trace_add("write", self.filter_data)

        tk.Label(self.root, text="Filter Nama Produk:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.filter_nama_produk).pack(pady=5)

        # --- Tombol Refresh ---
        self.btn_refresh = tk.Button(self.root, text="Refresh Data", command=self.refresh_data)
        self.btn_refresh.pack(pady=5)

        # --- Tabel ---
        self.frame_tabel = tk.Frame(self.root)
        self.frame_tabel.pack(padx=10, pady=10, fill="both", expand=True)
        self.buat_tabel()

        # --- Tombol Edit dan Hapus ---
        frame_tombol = tk.Frame(self.root)
        frame_tombol.pack(pady=10)

        self.btn_edit_varian = tk.Button(frame_tombol, text="Edit Varian", command=self.edit_varian, state="disabled")
        self.btn_edit_varian.pack(side="left", padx=5)
        self.btn_hapus_varian = tk.Button(frame_tombol, text="Hapus Varian", command=self.hapus_varian, state="disabled")
        self.btn_hapus_varian.pack(side="left", padx=5)
        self.btn_tambah_varian = tk.Button(frame_tombol, text="Tambah Varian", command=self.tambah_varian, state="disabled")
        self.btn_tambah_varian.pack(side="left", padx=5)
        self.btn_edit_produk = tk.Button(frame_tombol, text="Edit Produk", command=self.edit_produk, state="disabled")
        self.btn_edit_produk.pack(side="left", padx=5)
        self.btn_hapus_produk = tk.Button(frame_tombol, text="Hapus Produk", command=self.hapus_produk, state="disabled")
        self.btn_hapus_produk.pack(side="left", padx=5)

        self.tabel.bind("<<TreeviewSelect>>", self.on_tabel_select)

    def buat_tabel(self):
        """Membuat tabel untuk menampilkan data produk (window filter)."""
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

        self.refresh_data()  # Load data on startup

    def refresh_data(self):
        """Mengambil data terbaru dari database dan memperbarui tabel."""
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()
        cursor.execute("SELECT kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian FROM produk")
        self.data_produk_temp = cursor.fetchall()
        conn.close()

        # Filter data jika ada keyword filter
        self.filter_data()
        messagebox.showinfo("Info", "Data berhasil di-refresh dari database!")

    def filter_data(self, *args):
        """Memfilter data di tabel berdasarkan nama produk."""
        keyword = self.filter_nama_produk.get().lower()

        # Ambil data dari database jika keyword kosong
        if not keyword:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()
            cursor.execute("SELECT kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian FROM produk")
            self.data_produk_temp = cursor.fetchall()
            conn.close()
            filtered_data = self.data_produk_temp
        else:
            # Filter data menggunakan SequenceMatcher untuk fleksibilitas
            filtered_data = [
                item for item in self.data_produk_temp
                if SequenceMatcher(None, keyword, item[1].lower()).ratio() >= 0.6
            ]

        # Update tabel
        for row in self.tabel.get_children():
            self.tabel.delete(row)
        for data in filtered_data:
            self.tabel.insert("", tk.END, values=data)

    def on_tabel_select(self, event):
        """Menangani event saat baris tabel dipilih."""
        self.root.after(100, self.delayed_on_tabel_select)

    def delayed_on_tabel_select(self):
        selected_items = self.tabel.selection()
        if selected_items:
            # Aktifkan tombol Edit dan Hapus
            self.btn_edit_varian.config(state="normal")
            self.btn_hapus_varian.config(state="normal")
            self.btn_tambah_varian.config(state="normal")
            self.btn_edit_produk.config(state="normal")
            self.btn_hapus_produk.config(state="normal")
        else:
            # Nonaktifkan tombol Edit dan Hapus
            self.btn_edit_varian.config(state="disabled")
            self.btn_hapus_varian.config(state="disabled")
            self.btn_tambah_varian.config(state="disabled")
            self.btn_edit_produk.config(state="disabled")
            self.btn_hapus_produk.config(state="disabled")

    def edit_varian(self):
        """Membuka window untuk mengedit varian yang dipilih."""
        selected_item = self.tabel.selection()[0]
        data_varian = self.tabel.item(selected_item)['values']

        window_edit_varian = tk.Toplevel(self.root)
        window_edit_varian.title("Edit Varian")
        EditVarianWindow(window_edit_varian, data_varian, self.update_varian_callback, self.refresh_data_callback)

    def update_varian_callback(self, updated_data):
        """Callback function to update variant data after editing."""
        barcode = updated_data[4]
        nama_varian_baru = updated_data[6]

        # Update data di database
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE produk SET nama_varian = ? WHERE barcode = ?", (nama_varian_baru, barcode))
        conn.commit()
        conn.close()

        # Perbarui data_produk_temp
        for i, item in enumerate(self.data_produk_temp):
            if item[4] == barcode:
                self.data_produk_temp[i] = updated_data
                break

        # Update tabel
        self.refresh_data_callback()  # Memanggil filter_data untuk refresh tampilan tabel

        # Catat log
        catat_log('EDIT VARIAN', str(data_lama), str(updated_data), f'Varian diubah dari {nama_varian_lama} menjadi {nama_varian_baru}')

    def hapus_varian(self):
        """Menghapus varian yang dipilih."""
        selected_item = self.tabel.selection()[0]
        data_varian = self.tabel.item(selected_item)['values']
        barcode = data_varian[4]

        # Konfirmasi hapus
        if messagebox.askyesno("Konfirmasi", f"Yakin ingin menghapus varian {data_varian[6]}?"):
            try:
                # Hapus data dari database
                conn = sqlite3.connect('produk.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM produk WHERE barcode = ?", (barcode,))
                conn.commit()
                conn.close()

                # Cari data_lama sebelum menghapus dari self.data_produk_temp
                data_lama = None
                for item in self.data_produk_temp:
                    if item[4] == barcode:
                        data_lama = item
                        break

                # Hapus data dari data_produk_temp
                self.data_produk_temp = [item for item in self.data_produk_temp if item[4] != barcode]

                # Update tabel
                self.refresh_data_callback()
                messagebox.showinfo("Info", "Varian berhasil dihapus!")

                # Catat log
                catat_log('HAPUS VARIAN', str(data_lama), None, f'Varian {data_varian[6]} dihapus')

            except Exception as e:
                messagebox.showerror("Error", f"Terjadi kesalahan: {e}")

    def tambah_varian(self):
        """Membuka window untuk menambah varian baru."""
        selected_item = self.tabel.selection()[0]
        data_produk = self.tabel.item(selected_item)['values']
        kode_produk = data_produk[0]
        nama_produk = data_produk[1]
        deskripsi = data_produk[2]
        kode_toko = data_produk[3]

        window_tambah_varian = tk.Toplevel(self.root)
        window_tambah_varian.title("Tambah Varian")
        TambahVarianWindow(window_tambah_varian, kode_produk, nama_produk, deskripsi, kode_toko, self.refresh_data)


    def edit_produk(self):
        """Membuka window untuk mengedit produk yang dipilih."""
        selected_item = self.tabel.selection()[0]
        data_produk = self.tabel.item(selected_item)['values']

        window_edit_produk = tk.Toplevel(self.root)
        window_edit_produk.title("Edit Produk")
        EditProdukWindow(window_edit_produk, data_produk, self.update_produk_callback, self.refresh_data_callback)

    def update_produk_callback(self, updated_data):
        """Callback function to update product data after editing."""
        kode_produk = updated_data[0]
        nama_produk_baru = updated_data[1]
        deskripsi_baru = updated_data[2]
        kode_toko_baru = updated_data[3]

        # Update data di database
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE produk SET nama_produk = ?, deskripsi = ?, kode_toko = ? WHERE kode_produk = ?",
            (nama_produk_baru, deskripsi_baru, kode_toko_baru, kode_produk)
        )
        conn.commit()
        conn.close()

        # Perbarui data_produk_temp
        for i, item in enumerate(self.data_produk_temp):
            if item[0] == kode_produk:
                self.data_produk_temp[i] = (
                    kode_produk,
                    nama_produk_baru,
                    deskripsi_baru,
                    kode_toko_baru,
                    item[4],  # barcode tetap
                    item[5],  # kode_varian tetap
                    item[6]   # nama_varian tetap
                )

        # Update tabel
        self.refresh_data_callback()

        # Catat log
        catat_log('EDIT PRODUK', str(data_lama), str(updated_data), f'Produk diubah dari nama: {nama_produk_lama}, deskripsi: {deskripsi_lama}, kode toko: {kode_toko_lama} menjadi nama: {nama_produk_baru}, deskripsi: {deskripsi_baru}, kode toko: {kode_toko_baru}')

    def hapus_produk(self):
        """Menghapus produk yang dipilih."""
        selected_item = self.tabel.selection()[0]
        data_produk = self.tabel.item(selected_item)['values']
        kode_produk = data_produk[0]

        # Konfirmasi hapus
        if messagebox.askyesno("Konfirmasi", f"Yakin ingin menghapus produk {data_produk[1]} beserta semua variannya?"):
            try:
                # Hapus data dari database
                conn = sqlite3.connect('produk.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM produk WHERE kode_produk = ?", (kode_produk,))
                conn.commit()
                conn.close()

                # Hapus data dari data_produk_temp
                data_lama = [item for item in self.data_produk_temp if item[0] == kode_produk]
                self.data_produk_temp = [item for item in self.data_produk_temp if item[0] != kode_produk]

                # Update tabel
                self.refresh_data_callback()
                messagebox.showinfo("Info", "Produk berhasil dihapus!")

                # Catat log
                catat_log('HAPUS PRODUK', str(data_lama), None, f'Produk {data_produk[1]} dan semua variannya dihapus')

            except Exception as e:
                messagebox.showerror("Error", f"Terjadi kesalahan: {e}")

    def refresh_data_callback(self):
        """Callback function to refresh data after editing."""
        self.refresh_data()

class EditVarianWindow:
    def __init__(self, root, data_varian, update_callback, refresh_parent_data):
        self.root = root
        self.data_varian = data_varian
        self.update_callback = update_callback
        self.refresh_parent_data = refresh_parent_data

        # Label dan Entry untuk edit varian
        tk.Label(self.root, text="Nama Produk:").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.root, text=data_varian[1]).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Kode Varian:").grid(row=1, column=0, padx=5, pady=5)
        tk.Label(self.root, text=data_varian[5]).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Nama Varian:").grid(row=2, column=0, padx=5, pady=5)
        self.entry_nama_varian = tk.Entry(self.root)
        self.entry_nama_varian.insert(0, data_varian[6])
        self.entry_nama_varian.grid(row=2, column=1, padx=5, pady=5)

        # Tombol Simpan
        btn_simpan = tk.Button(self.root, text="Simpan", command=self.simpan_perubahan)
        btn_simpan.grid(row=3, column=0, columnspan=2, pady=10)

    def simpan_perubahan(self):
        """Menyimpan perubahan varian."""
        nama_varian_baru = self.entry_nama_varian.get()

        # Validasi input
        if not nama_varian_baru:
            messagebox.showerror("Error", "Nama varian tidak boleh kosong!")
            return

        # Update data
        updated_data = list(self.data_varian)
        updated_data[6] = nama_varian_baru

        # Panggil callback untuk update di database dan tabel
        self.update_callback(updated_data)

        # Tutup window edit
        self.root.destroy()

class TambahVarianWindow:
    def __init__(self, root, kode_produk, nama_produk, deskripsi, kode_toko, refresh_parent_data):
        self.root = root
        self.kode_produk = kode_produk
        self.nama_produk = nama_produk
        self.deskripsi = deskripsi
        self.kode_toko = kode_toko
        self.refresh_parent_data = refresh_parent_data

        tk.Label(self.root, text="Nama Produk:").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.root, text=nama_produk).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Nama Varian:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_nama_varian = tk.Entry(self.root)
        self.entry_nama_varian.grid(row=1, column=1, padx=5, pady=5)

        # Tombol Simpan
        btn_simpan = tk.Button(self.root, text="Simpan", command=self.simpan_varian)
        btn_simpan.grid(row=2, column=0, columnspan=2, pady=10)

    def simpan_varian(self):
        """Menyimpan varian baru ke database."""
        nama_varian = self.entry_nama_varian.get()

        if not nama_varian:
            messagebox.showerror("Error", "Nama varian tidak boleh kosong!")
            return

        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()

        # Check if the variant already exists
        cursor.execute("SELECT COUNT(*) FROM produk WHERE kode_produk = ? AND nama_varian = ?", (self.kode_produk, nama_varian))
        count = cursor.fetchone()[0]
        if count > 0:
            messagebox.showerror("Error", "Varian dengan nama tersebut sudah ada untuk produk ini!")
            conn.close()
            return

        # Generate new barcode
        while True:
            kode_varian = ''.join(random.choices('0123456789', k=4))
            barcode = str(self.kode_toko) + self.kode_produk[-5:] + kode_varian
            cursor.execute("SELECT COUNT(*) FROM produk WHERE barcode = ?", (barcode,))
            count = cursor.fetchone()[0]
            if count == 0:
                break

        try:
            cursor.execute(
                "INSERT INTO produk (kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.kode_produk, self.nama_produk, self.deskripsi, self.kode_toko, barcode, kode_varian, nama_varian)
            )
            conn.commit()
            messagebox.showinfo("Info", "Varian berhasil ditambahkan!")
            self.root.destroy()
            self.refresh_parent_data()

            # Catat log setelah varian baru ditambahkan
            catat_log('TAMBAH VARIAN', None, str((self.kode_produk, self.nama_produk, self.deskripsi, self.kode_toko, barcode, kode_varian, nama_varian)), f'Varian {nama_varian} ditambahkan ke produk {self.nama_produk}')

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        finally:
            conn.close()

class EditProdukWindow:
    def __init__(self, root, data_produk, update_callback, refresh_parent_data):
        self.root = root
        self.data_produk = data_produk
        self.update_callback = update_callback
        self.refresh_parent_data = refresh_parent_data

        # Label dan Entry untuk edit produk
        tk.Label(self.root, text="Kode Produk:").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.root, text=data_produk[0]).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Nama Produk:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_nama_produk = tk.Entry(self.root)
        self.entry_nama_produk.insert(0, data_produk[1])
        self.entry_nama_produk.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Deskripsi:").grid(row=2, column=0, padx=5, pady=5)
        self.entry_deskripsi = tk.Entry(self.root)
        self.entry_deskripsi.insert(0, data_produk[2])
        self.entry_deskripsi.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Kode Toko:").grid(row=3, column=0, padx=5, pady=5)
        self.kode_toko_options = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        self.kode_toko = tk.StringVar(value=data_produk[3])
        tk.OptionMenu(self.root, self.kode_toko, *self.kode_toko_options).grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Tombol Simpan
        btn_simpan = tk.Button(self.root, text="Simpan", command=self.simpan_perubahan)
        btn_simpan.grid(row=4, column=0, columnspan=2, pady=10)

    def simpan_perubahan(self):
        """Menyimpan perubahan produk."""
        nama_produk_baru = self.entry_nama_produk.get()
        deskripsi_baru = self.entry_deskripsi.get()
        kode_toko_baru = self.kode_toko.get()

        # Validasi input
        if not nama_produk_baru or not deskripsi_baru:
            messagebox.showerror("Error", "Nama produk dan deskripsi tidak boleh kosong!")
            return

        # Update data
        updated_data = list(self.data_produk)
        updated_data[1] = nama_produk_baru
        updated_data[2] = deskripsi_baru
        updated_data[3] = kode_toko_baru

        # Panggil callback untuk update di database dan tabel
        self.update_callback(updated_data)

        # Tutup window edit
        self.root.destroy()
        self.refresh_parent_data()

if __name__ == "__main__":
    root = tk.Tk()
    aplikasi = WindowFilter(root)
    root.mainloop()