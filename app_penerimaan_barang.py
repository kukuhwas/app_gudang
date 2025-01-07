import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from ttkbootstrap import DateEntry, Style
from datetime import date
import random
from database import ambil_semua_supplier

class WindowPenerimaanBarang:
    def __init__(self, root):
        self.root = root
        self.root.title("Surat Penerimaan Barang")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Style
        self.style = Style(theme='cosmo')

        # --- Header Form ---
        self.frame_header = ttk.LabelFrame(self.root, text="Header", style="primary.TLabelframe")
        self.frame_header.pack(padx=10, pady=10, fill="x")

        # No. Penerimaan (otomatis)
        ttk.Label(self.frame_header, text="No. Penerimaan:", style="TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.no_penerimaan = tk.StringVar()
        ttk.Label(self.frame_header, textvariable=self.no_penerimaan, style="TLabel").grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Tanggal
        ttk.Label(self.frame_header, text="Tanggal:", style="TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tanggal = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        self.entry_tanggal = DateEntry(self.frame_header, bootstyle="primary")
        self.entry_tanggal.grid(row=1, column=1, padx=5, pady=5)
        self.entry_tanggal.bind("<<DateEntrySelected>>", self.update_tanggal)

        # Supplier
        ttk.Label(self.frame_header, text="Supplier:", style="TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.supplier_id = tk.StringVar()
        self.supplier_options = self.get_supplier_options()
        self.combobox_supplier = ttk.Combobox(self.frame_header, textvariable=self.supplier_id, values=self.supplier_options, state="readonly", style="primary.TCombobox")
        self.combobox_supplier.grid(row=2, column=1, padx=5, pady=5)

        # Keterangan
        ttk.Label(self.frame_header, text="Keterangan:", style="TLabel").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.keterangan = tk.StringVar()
        ttk.Entry(self.frame_header, textvariable=self.keterangan, style="TEntry").grid(row=3, column=1, padx=5, pady=5)

        # --- Tabel ---
        self.frame_tabel = ttk.Frame(self.root)
        self.frame_tabel.pack(padx=10, pady=10, fill="both", expand=True)
        self.buat_tabel()

        # --- Tombol ---
        frame_tombol = ttk.Frame(self.root)
        frame_tombol.pack(pady=10)
        ttk.Button(frame_tombol, text="Tambah Barang", command=self.tambah_barang, style="success.TButton").pack(side="left", padx=5)
        ttk.Button(frame_tombol, text="Simpan", command=self.simpan_penerimaan, style="primary.TButton").pack(side="left", padx=5)

        # --- Total QTY ---
        self.frame_total = ttk.Frame(self.root)
        self.frame_total.pack(padx=10, pady=5, fill="x")
        self.total_qty_label = ttk.Label(self.frame_total, text="Total QTY: 0", style="TLabel")
        self.total_qty_label.pack(side="right")

        # Generate nomor penerimaan
        self.generate_no_penerimaan()

    def buat_tabel(self):
        """Membuat tabel untuk input barang."""
        self.tabel = ttk.Treeview(self.frame_tabel, columns=("barcode", "nama_barang", "varian", "qty", "keterangan"), show="headings", style="Treeview")
        self.tabel.pack(fill="both", expand=True)

        self.tabel.heading("barcode", text="Barcode")
        self.tabel.heading("nama_barang", text="Nama Barang")
        self.tabel.heading("varian", text="Varian")
        self.tabel.heading("qty", text="QTY")
        self.tabel.heading("keterangan", text="Keterangan")

        self.tabel.column("barcode", width=150)
        self.tabel.column("nama_barang", width=200)
        self.tabel.column("varian", width=150)
        self.tabel.column("qty", width=50)
        self.tabel.column("keterangan", width=200)

        yscrollbar = ttk.Scrollbar(self.frame_tabel, orient="vertical", command=self.tabel.yview)
        yscrollbar.pack(side="right", fill="y")

        self.tabel.configure(yscrollcommand=yscrollbar.set)
        self.tabel.configure(xscrollcommand="")

        # Styling Tabel
        style = ttk.Style()
        style.configure("Treeview",
                        background="#e1e1e1",
                        foreground="black",
                        rowheight=25,
                        fieldbackground="#e1e1e1",
                        bordercolor="#606060",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background="#005f73",
                        foreground="white",
                        relief="flat",
                        font=('Helvetica', 10, 'bold'))
        style.map("Treeview",
                  background=[("selected", "#005f73")],
                  foreground=[("selected", "white")])

    def get_supplier_options(self):
        """Mengambil data supplier dari database."""
        suppliers = ambil_semua_supplier()
        return [f"{sup[0]} - {sup[1]}" for sup in suppliers]

    def generate_no_penerimaan(self):
        """Membuat nomor penerimaan barang secara otomatis."""
        # Format: PB-YYYYMMDD-XXXX (X adalah angka random)
        today = date.today().strftime('%Y%m%d')
        random_num = ''.join(random.choices('0123456789', k=4))
        self.no_penerimaan.set(f"PB-{today}-{random_num}")

    def tambah_barang(self):
        """Membuka window untuk menambah barang."""
        window_tambah = tk.Toplevel(self.root)
        window_tambah.title("Tambah Barang")
        TambahBarangWindow(window_tambah, self.tabel, self.refresh_total_qty, self.style)

    def refresh_total_qty(self):
        """Memperbarui total QTY."""
        total_qty = 0
        for item in self.tabel.get_children():
            values = self.tabel.item(item, 'values')
            if values:
                try:
                    qty = int(values[3])
                    total_qty += qty
                except ValueError:
                    pass

        self.total_qty_label.config(text=f"Total QTY: {total_qty}")

    def update_tanggal(self, event):
        """Update variabel tanggal dengan tanggal yang dipilih."""
        self.tanggal.set(self.entry_tanggal.get_date().strftime('%Y-%m-%d'))

    def simpan_penerimaan(self):
        """Menyimpan data penerimaan barang ke database."""
        no_penerimaan = self.no_penerimaan.get()
        tanggal = self.tanggal.get()
        supplier = self.supplier_id.get()
        keterangan = self.keterangan.get()

        # Validasi
        if not no_penerimaan:
            messagebox.showerror("Error", "Nomor penerimaan tidak valid!")
            return
        if not tanggal:
            messagebox.showerror("Error", "Tanggal harus diisi!")
            return
        if not supplier:
            messagebox.showerror("Error", "Supplier harus dipilih!")
            return
        if not self.tabel.get_children():
            messagebox.showerror("Error", "Tambahkan barang terlebih dahulu!")
            return

        # Ambil data detail barang
        detail_barang = []
        for item in self.tabel.get_children():
            values = self.tabel.item(item, 'values')
            detail_barang.append(values)

        supplier_id = int(supplier.split(" - ")[0])

        conn = None
        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()

            # Simpan data ke tabel penerimaan_barang
            cursor.execute("INSERT INTO penerimaan_barang (no_penerimaan, tanggal, supplier_id, keterangan) VALUES (?, ?, ?, ?)",
                           (no_penerimaan, tanggal, supplier_id, keterangan))

            # Simpan data ke tabel detail_penerimaan dan update stok
            for barang in detail_barang:
                barcode = barang[0]
                qty = int(barang[3])

                cursor.execute("INSERT INTO detail_penerimaan (no_penerimaan, barcode, qty) VALUES (?, ?, ?)",
                               (no_penerimaan, barcode, qty))

                # Cek apakah barang sudah ada di tabel stok
                cursor.execute("SELECT qty_stok FROM stok WHERE barcode = ?", (barcode,))
                row = cursor.fetchone()
                if row:
                    # Update stok
                    new_qty = row[0] + qty
                    cursor.execute("UPDATE stok SET qty_stok = ? WHERE barcode = ?", (new_qty, barcode))
                else:
                    # Tambah barang ke tabel stok
                    cursor.execute("INSERT INTO stok (barcode, qty_stok) VALUES (?, ?)", (barcode, qty))

            conn.commit()
            messagebox.showinfo("Info", "Data penerimaan barang berhasil disimpan!")
            self.clear_form()

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        finally:
            if conn:
                conn.close()

    def clear_form(self):
        """Membersihkan form."""
        self.generate_no_penerimaan()
        self.tanggal.set(date.today().strftime('%Y-%m-%d'))
        self.combobox_supplier.set("")
        self.keterangan.set("")
        for row in self.tabel.get_children():
            self.tabel.delete(row)
        self.refresh_total_qty()


class AutoSuggestEntry(ttk.Entry):
    def __init__(self, master=None, suggest_function=None, **kwargs):
        super().__init__(master, **kwargs)
        self.suggest_function = suggest_function
        self.listbox = None
        self.bind("<KeyRelease>", self.handle_keyrelease)
        self.bind("<FocusOut>", self.hide_listbox)

    def handle_keyrelease(self, event):
        """Menangani event KeyRelease untuk auto-suggestion."""
        if event.keysym == "Down":
            self.focus_listbox()
        else:
            typed = self.get()
            if typed == '':
                self.hide_listbox()
            else:
                suggestions = self.suggest_function(typed)
                if suggestions:
                    self.show_listbox(suggestions)
                else:
                    self.hide_listbox()

    def show_listbox(self, suggestions):
        """Menampilkan listbox dengan sugesti."""
        if not self.listbox:
            self.listbox = tk.Listbox(self.master)
            self.listbox.place(x=self.winfo_x(), y=self.winfo_y() + self.winfo_height())
            self.listbox.bind("<<ListboxSelect>>", self.fill_from_listbox)
        self.listbox.delete(0, tk.END)
        for item in suggestions:
            self.listbox.insert(tk.END, item)

    def fill_from_listbox(self, event):
        """Mengisi entry dengan item yang dipilih dari listbox."""
        try:
            index = self.listbox.curselection()[0]
            selected_item = self.listbox.get(index)
            self.delete(0, tk.END)
            self.insert(0, selected_item)
            self.hide_listbox()
        except IndexError:
            pass

    def focus_listbox(self):
        """Memberikan fokus ke listbox."""
        if self.listbox:
            self.listbox.focus_set()
            self.listbox.selection_set(0)

    def hide_listbox(self, event=None):
        """Menyembunyikan listbox."""
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None

class TambahBarangWindow:
    def __init__(self, root, tabel, refresh_total_qty_callback):
        self.root = root
        self.tabel = tabel
        self.refresh_total_qty_callback = refresh_total_qty_callback
        self.data_produk = []
        self.nama_produk_list = []
        self.varian_produk_list = []
        self.suggestions = []
        self.varian_suggestions = []
        self.selected_product = tk.StringVar()
        self.selected_varian = tk.StringVar()
        self.selected_qty = tk.StringVar()
        self.selected_keterangan = tk.StringVar()

        ttk.Label(self.root, text="Nama Barang:", style="TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nama_barang_entry = ttk.Entry(self.root, style="TEntry")
        self.nama_barang_entry.grid(row=0, column=1, padx=5, pady=5)
        self.nama_barang_entry.bind("<KeyRelease>", self.update_suggestions)
        # Pemicu event saat focus in
        self.nama_barang_entry.bind("<FocusIn>", lambda event: self.nama_barang_entry.event_generate('<KeyRelease>'))
        # Pemicu event saat focus out
        self.nama_barang_entry.bind("<FocusOut>", lambda event: self.hide_listbox())

        self.listbox_suggestions = tk.Listbox(self.root)
        self.listbox_suggestions.grid(row=1, column=1, padx=5, sticky="ew")
        self.listbox_suggestions.bind("<<ListboxSelect>>", self.fill_entry_from_listbox)

        ttk.Label(self.root, text="Varian Warna:", style="TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.varian_entry = ttk.Entry(self.root, textvariable=self.selected_varian, style="TEntry")
        self.varian_entry.grid(row=2, column=1, padx=5, pady=5)
        self.varian_entry.bind("<KeyRelease>", self.update_varian_suggestions)
        self.varian_entry.bind("<FocusIn>", lambda event: self.varian_entry.event_generate('<KeyRelease>'))
        # Pemicu event saat focus out
        self.varian_entry.bind("<FocusOut>", lambda event: self.hide_varian_listbox())

        self.listbox_varian_suggestions = tk.Listbox(self.root)
        self.listbox_varian_suggestions.grid(row=3, column=1, padx=5, sticky="ew")
        self.listbox_varian_suggestions.bind("<<ListboxSelect>>", self.fill_varian_entry_from_listbox)

        ttk.Label(self.root, text="QTY:", style="TLabel").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.root, textvariable=self.selected_qty, style="TEntry").grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(self.root, text="Keterangan:", style="TLabel").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.root, textvariable=self.selected_keterangan, style="TEntry").grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(self.root, text="Tambah", command=self.tambah_ke_tabel, style="success.TButton").grid(row=6, column=0, columnspan=2, pady=10)

        # Load data produk for suggestions
        self.update_nama_produk_list()
        self.selected_product.trace("w", self.on_nama_barang_selected)

    def update_nama_produk_list(self):
        """Mengambil data nama barang dari database."""
        conn = None
        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT nama_produk FROM produk")
            self.nama_produk_list = [item[0] for item in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        finally:
            if conn:
                conn.close()
    
    def hide_listbox(self, event=None):
        """Menyembunyikan listbox."""
        self.listbox_suggestions.delete(0, tk.END)
    
    def hide_varian_listbox(self, event=None):
        """Menyembunyikan listbox varian."""
        self.listbox_varian_suggestions.delete(0, tk.END)

    def update_suggestions(self, event):
        """Memberikan sugesti nama produk berdasarkan input."""
        typed = self.nama_barang_entry.get()
        if typed == '':
            self.suggestions = self.nama_produk_list
        else:
            self.suggestions = [item for item in self.nama_produk_list if typed.lower() in item.lower()]
        
        # Batasi hanya 10 sugesti
        self.suggestions = self.suggestions[:10]

        self.update_listbox()
        self.listbox_suggestions.config(height=min(10, len(self.suggestions)))

    def update_listbox(self):
        """Update listbox dengan sugesti."""
        self.listbox_suggestions.delete(0, tk.END)
        for item in self.suggestions:
            self.listbox_suggestions.insert(tk.END, item)

    def fill_entry_from_listbox(self, event):
        """Mengisi entry nama barang dengan pilihan dari listbox."""
        try:
            if self.listbox_suggestions.curselection():
              index = self.listbox_suggestions.curselection()[0]
              selected_item = self.suggestions[index]
              self.nama_barang_entry.delete(0, tk.END)
              self.nama_barang_entry.insert(0, selected_item)
              self.selected_product.set(selected_item)
              self.on_nama_barang_selected()
              self.listbox_suggestions.delete(0, tk.END)
        except IndexError:
            pass
    
    def update_varian_produk_list(self, nama_barang):
        """Mengambil data varian dari database berdasarkan nama barang."""
        conn = None
        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT nama_varian FROM produk WHERE nama_produk = ?", (nama_barang,))
            self.varian_produk_list = [item[0] for item in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        finally:
            if conn:
                conn.close()

    def update_varian_suggestions(self, event):
        """Memberikan sugesti varian berdasarkan input."""
        nama_barang = self.nama_barang_entry.get()
        self.update_varian_produk_list(nama_barang)
        typed = self.varian_entry.get()
        if typed == '':
            self.varian_suggestions = self.varian_produk_list
        else:
            self.varian_suggestions = [item for item in self.varian_produk_list if typed.lower() in item.lower()]

        self.update_varian_listbox()

    def update_varian_listbox(self):
        """Update listbox varian dengan sugesti."""
        self.listbox_varian_suggestions.delete(0, tk.END)
        for item in self.varian_suggestions:
            self.listbox_varian_suggestions.insert(tk.END, item)

    def fill_varian_entry_from_listbox(self, event):
        """Mengisi entry varian dengan pilihan dari listbox."""
        try:
            index = self.listbox_varian_suggestions.curselection()[0]
            selected_item = self.varian_suggestions[index]
            self.varian_entry.delete(0, tk.END)
            self.varian_entry.insert(0, selected_item)
            self.selected_varian.set(selected_item)
            self.listbox_varian_suggestions.delete(0, tk.END)
        except IndexError:
            pass
    
    def on_nama_barang_selected(self, *args):
        """Mengambil varian yang tersedia untuk produk yang dipilih."""
        nama_barang = self.selected_product.get()
        if nama_barang:
            conn = None
            try:
                conn = sqlite3.connect('produk.db')
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT nama_varian FROM produk WHERE nama_produk=?", (nama_barang,))
                varian = cursor.fetchall()
                self.varian_produk_list = [item[0] for item in varian]
            except Exception as e:
                messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
            finally:
                if conn:
                    conn.close()
        else:
            self.varian_produk_list = []

        self.update_varian_suggestions(None)

    def tambah_ke_tabel(self):
        """Menambahkan barang ke tabel."""
        nama_barang = self.nama_barang_entry.get()
        varian = self.selected_varian.get()
        qty = self.selected_qty.get()
        keterangan = self.selected_keterangan.get()

        # Ambil barcode dari database
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()
        cursor.execute("SELECT barcode FROM produk WHERE nama_produk = ? AND nama_varian = ?", (nama_barang, varian))
        result = cursor.fetchone()
        conn.close()

        if result:
            barcode = result[0]
        else:
            messagebox.showerror("Error", "Barcode tidak ditemukan untuk produk dan varian yang dipilih.")
            return

        if not barcode or not nama_barang or not varian or not qty:
            messagebox.showerror("Error", "Semua field harus diisi!")
            return

        try:
            qty = int(qty)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "QTY harus berupa angka dan lebih besar dari 0!")
            return

        self.tabel.insert("", tk.END, values=(barcode, nama_barang, varian, qty, keterangan))
        self.refresh_total_qty_callback()
        self.root.destroy()
        
if __name__ == "__main__":
    root = tk.Tk()
    aplikasi = WindowPenerimaanBarang(root)
    root.mainloop()
