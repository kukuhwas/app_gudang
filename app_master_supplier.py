import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class WindowMasterSupplier:
    def __init__(self, root):
        self.root = root
        self.root.title("Master Supplier")

        # --- Variabel ---
        self.nama_supplier = tk.StringVar()
        self.kategori_supplier = tk.StringVar(value="Penjahit")  # Default value

        # --- Frame Input ---
        frame_input = tk.LabelFrame(self.root, text="Input Data Supplier")
        frame_input.pack(padx=10, pady=10, fill="x")

        tk.Label(frame_input, text="Nama Supplier:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(frame_input, textvariable=self.nama_supplier).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame_input, text="Kategori:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        frame_radio = tk.Frame(frame_input)
        frame_radio.grid(row=2, column=1, padx=5, pady=5)
        tk.Radiobutton(frame_radio, text="Penjahit", variable=self.kategori_supplier, value="Penjahit").pack(side="left")
        tk.Radiobutton(frame_radio, text="Barang Jadi", variable=self.kategori_supplier, value="Barang Jadi").pack(side="left")

        # --- Tombol ---
        frame_tombol = tk.Frame(self.root)
        frame_tombol.pack(pady=10)
        tk.Button(frame_tombol, text="Simpan", command=self.simpan_data).pack(side="left", padx=5)
        tk.Button(frame_tombol, text="Update", command=self.update_data).pack(side="left", padx=5)
        tk.Button(frame_tombol, text="Hapus", command=self.hapus_data).pack(side="left", padx=5)
        tk.Button(frame_tombol, text="Clear", command=self.clear_input).pack(side="left", padx=5)

        # --- Tabel ---
        self.frame_tabel = tk.Frame(self.root)
        self.frame_tabel.pack(padx=10, pady=10, fill="both", expand=True)
        self.buat_tabel()
        self.refresh_data()

    def buat_tabel(self):
        """Membuat tabel untuk menampilkan data supplier."""
        self.tabel = ttk.Treeview(self.frame_tabel, columns=("id_supplier", "nama", "kategori"), show="headings")
        self.tabel.pack(fill="both", expand=True)

        self.tabel.heading("id_supplier", text="ID Supplier")
        self.tabel.heading("nama", text="Nama Supplier")
        self.tabel.heading("kategori", text="Kategori")

        self.tabel.column("id_supplier", width=100)
        self.tabel.column("nama", width=200)
        self.tabel.column("kategori", width=150)

        yscrollbar = ttk.Scrollbar(self.frame_tabel, orient="vertical", command=self.tabel.yview)
        yscrollbar.pack(side="right", fill="y")
        self.tabel.configure(yscrollcommand=yscrollbar.set)

        self.tabel.bind("<<TreeviewSelect>>", self.on_tabel_select)

    def refresh_data(self):
        """Mengambil data supplier dari database dan memperbarui tabel."""
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM supplier")
        self.data_supplier = cursor.fetchall()  # Menyimpan ke self.data_supplier
        conn.close()

        for row in self.tabel.get_children():
            self.tabel.delete(row)
        for data in self.data_supplier:  # Menggunakan self.data_supplier
            self.tabel.insert("", tk.END, values=data)

    def simpan_data(self):
        """Menyimpan data supplier ke database."""
        nama = self.nama_supplier.get()
        kategori = self.kategori_supplier.get()

        if not nama:
            messagebox.showerror("Error", "Nama Supplier harus diisi!")
            return

        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO supplier (nama, kategori) VALUES (?, ?)", (nama, kategori))  # Hapus id_supplier dari query
            conn.commit()
            conn.close()
            messagebox.showinfo("Info", "Data supplier berhasil disimpan!")
            self.clear_input()
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")


    def update_data(self):
        """Mengupdate data supplier di database."""
        selected_item = self.tabel.selection()
        if not selected_item:
            messagebox.showerror("Error", "Pilih baris data yang akan di-update!")
            return

        # Ambil data lama dari baris yang dipilih
        selected_index = self.tabel.index(selected_item[0])
        old_data = self.data_supplier[selected_index]

        # Ambil ID dari data lama
        id_supplier = old_data[0]
        nama = self.nama_supplier.get()
        kategori = self.kategori_supplier.get()

        if not nama:
            messagebox.showerror("Error", "Nama Supplier harus diisi!")
            return

        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE supplier SET nama = ?, kategori = ? WHERE id_supplier = ?", (nama, kategori, id_supplier))
            conn.commit()
            conn.close()
            messagebox.showinfo("Info", "Data supplier berhasil di-update!")
            self.clear_input()
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")

    def hapus_data(self):
        """Menghapus data supplier dari database."""
        selected_item = self.tabel.selection()
        if not selected_item:
            messagebox.showerror("Error", "Pilih baris data yang akan dihapus!")
            return

        # Ambil data lama dari baris yang dipilih
        selected_index = self.tabel.index(selected_item[0])
        old_data = self.data_supplier[selected_index]

        # Ambil ID dari data lama
        id_supplier = old_data[0]

        if messagebox.askyesno("Konfirmasi", f"Yakin ingin menghapus supplier dengan ID {id_supplier}?"):
            try:
                conn = sqlite3.connect('produk.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM supplier WHERE id_supplier = ?", (id_supplier,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Info", "Data supplier berhasil dihapus!")
                self.clear_input()
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", f"Terjadi kesalahan: {e}")

    def clear_input(self):
        """Membersihkan input fields."""
        self.nama_supplier.set("")
        self.kategori_supplier.set("Penjahit")

    def on_tabel_select(self, event):
        """Mengisi input fields dengan data dari baris tabel yang dipilih."""
        selected_item = self.tabel.selection()
        if selected_item:
            data = self.tabel.item(selected_item[0])['values']
            self.nama_supplier.set(data[1])
            self.kategori_supplier.set(data[2])

if __name__ == "__main__":
    root = tk.Tk()
    aplikasi = WindowMasterSupplier(root)
    root.mainloop()