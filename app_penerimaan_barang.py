import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from ttkbootstrap import DateEntry, Style
from datetime import date
import random

# Import untuk PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import webbrowser

# Import untuk Fuzzy Matching
from fuzzywuzzy import fuzz, process
from produk_db import ambil_semua_supplier, catat_log

class WindowPenerimaanBarang:
    def __init__(self, root):
        self.root = root
        self.root.title("Surat Penerimaan Barang")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Style
        self.style = Style(theme='cosmo')
        self.style.configure('Disabled.TEntry', foreground='black', fieldbackground='white')

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
        self.btn_simpan_saja = ttk.Button(frame_tombol, text="SIMPAN SAJA", command=lambda: self.simpan_penerimaan("simpan_saja"), style="primary.TButton")
        self.btn_simpan_saja.pack(side="left", padx=5)
        self.btn_simpan_pdf = ttk.Button(frame_tombol, text="SIMPAN & CETAK PDF", command=lambda: self.simpan_penerimaan("simpan_pdf"), style="secondary.TButton")
        self.btn_simpan_pdf.pack(side="left", padx=5)
        self.btn_simpan_print = ttk.Button(frame_tombol, text="SIMPAN & PRINT DOTMATRIX", command=lambda: self.simpan_penerimaan("simpan_print"), style="warning.TButton")
        self.btn_simpan_print.pack(side="left", padx=5)

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

    def generate_no_penerimaan(self):
        """Membuat nomor penerimaan barang secara otomatis dan berurutan."""
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()

        today = date.today().strftime('%Y%m')
        cursor.execute("SELECT nomor_terakhir FROM nomor_spb WHERE tahun_bulan = ?", (today,))
        result = cursor.fetchone()

        if result:
            nomor_terakhir = result[0]
            nomor_baru = nomor_terakhir + 1
            cursor.execute("UPDATE nomor_spb SET nomor_terakhir = ? WHERE tahun_bulan = ?", (nomor_baru, today))
        else:
            nomor_baru = 1
            cursor.execute("INSERT INTO nomor_spb (tahun_bulan, nomor_terakhir) VALUES (?, ?)", (today, nomor_baru))

        conn.commit()
        conn.close()

        self.no_penerimaan.set(f"PB-{today}{nomor_baru:04}")

    def tambah_barang(self):
        """Membuka window untuk menambah barang."""
        window_tambah = tk.Toplevel(self.root)
        window_tambah.title("Tambah Barang")
        window_tambah.geometry("400x350")
        TambahBarangWindow(window_tambah, self.tabel, self.refresh_total_qty, self.root)

    def simpan_penerimaan(self, action):
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

            # Mulai transaksi
            conn.execute("BEGIN")

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

            # Commit transaksi
            conn.commit()

            messagebox.showinfo("Info", "Data penerimaan barang berhasil disimpan!")

            # Cetak Surat Penerimaan Barang jika diminta
            if action == "simpan_pdf":
              self.cetak_surat_penerimaan(no_penerimaan, tanggal, supplier, keterangan, detail_barang)
            elif action == "simpan_print":
              self.cetak_epson_lx310(no_penerimaan, tanggal, supplier, keterangan, detail_barang)

            self.clear_form()

        except Exception as e:
            # Rollback transaksi jika terjadi kesalahan
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        finally:
            if conn:
                conn.close()

    def cetak_surat_penerimaan(self, no_penerimaan, tanggal, supplier, keterangan, detail_barang):
        """Menampilkan dialog untuk memilih jenis printer dan mencetak surat penerimaan barang."""
        # Buat dialog baru
        dialog = tk.Toplevel(self.root)
        dialog.title("Cetak Surat Penerimaan Barang")

        # Buat radio button untuk memilih jenis printer
        printer_type = tk.StringVar(value="pdf")  # Default ke PDF
        tk.Radiobutton(dialog, text="PDF", variable=printer_type, value="pdf").pack(pady=5)
        tk.Radiobutton(dialog, text="Epson LX-310 (Dot Matrix)", variable=printer_type, value="epson").pack(pady=5)

        # Fungsi untuk Konfigurasi Font
        def register_font(font_name, font_path):
            """Mendaftarkan font ke ReportLab."""
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                print(f"Font {font_name} berhasil didaftarkan.")
            except Exception as e:
                print(f"Gagal mendaftarkan font {font_name}: {e}")

        # Path lengkap ke file font
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, "fonts", "fonts/Consolas.ttf")
        font_bold_path = os.path.join(current_dir, "fonts", "fonts/consolab.ttf")

        # Konfigurasi Font
        register_font('Consolas', font_path)
        register_font('Consolas-Bold', font_bold_path)

        # Tombol Cetak
        def cetak():
            selected_printer = printer_type.get()
            dialog.destroy()  # Tutup dialog
            if selected_printer == "pdf":
                self.cetak_pdf(no_penerimaan, tanggal, supplier, keterangan, detail_barang)
            elif selected_printer == "epson":
                self.cetak_epson_lx310(no_penerimaan, tanggal, supplier, keterangan, detail_barang)

        tk.Button(dialog, text="Cetak", command=cetak).pack(pady=10)

    def cetak_pdf(self, no_penerimaan, tanggal, supplier, keterangan, detail_barang):
        """Membuat dan mencetak surat penerimaan barang dalam format PDF."""
        file_path = f"Surat_Penerimaan_{no_penerimaan}.pdf"

        c = canvas.Canvas(file_path, pagesize=letter)

        # Konfigurasi font
        c.setFont("Consolas-Bold", 14)  # Judul

        # Judul
        c.drawString(50, 750, "SURAT PENERIMAAN BARANG")
        c.setFont("Consolas", 10)

        # Header
        c.drawString(50, 730, f"No. Penerimaan : {no_penerimaan}")
        c.drawString(50, 715, f"Tanggal       : {tanggal}")
        c.drawString(50, 700, f"Supplier      : {supplier}")
        c.drawString(50, 685, f"Keterangan    : {keterangan}")

        # Tabel
        y = 650
        c.drawString(50, y, "---------------------------------------------------------------------")
        y -= 15
        c.drawString(50, y, "No. | Barcode        | Nama Barang              | Varian     | Qty")
        c.drawString(50, y - 5, "---------------------------------------------------------------------")
        y -= 20
        total_qty = 0

        # Mengambil data nama produk dan varian dari database
        conn = None
        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()

            for i, barang in enumerate(detail_barang):
                barcode, _, _, qty, _ = barang

                # Ambil nama produk dan varian dari database
                cursor.execute("SELECT nama_produk, nama_varian FROM produk WHERE barcode = ?", (barcode,))
                result = cursor.fetchone()
                if result:
                    nama_barang, varian = result
                else:
                    nama_barang, varian = "Tidak Diketahui", "Tidak Diketahui"

                c.drawString(50, y, f"{i+1:3} | {barcode:13} | {nama_barang:24} | {varian:10} | {qty:3}")
                y -= 15
                total_qty += int(qty)

            c.drawString(50, y, "---------------------------------------------------------------------")
            y -= 15
            c.drawString(50, y, f"Total Qty: {total_qty}")

            # Footer Tanda Tangan
            y -= 60
            c.drawString(70, y, "Penerima,")
            c.drawString(450, y, "Yang Menyerahkan,")
            y -= 60
            c.drawString(70, y, "(           )")
            c.drawString(450, y, "(           )")

            c.save()
            messagebox.showinfo("Info", f"Surat Penerimaan Barang berhasil dicetak ke {os.path.abspath(file_path)}")

            # Membuka file PDF setelah dibuat
            try:
                webbrowser.open_new(f"file://{os.path.abspath(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka PDF: {e}")

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat mencetak PDF: {e}")
        finally:
            if conn:
                conn.close()

    def cetak_epson_lx310(self, no_penerimaan, tanggal, supplier, keterangan, detail_barang):
        """Mencetak surat penerimaan barang ke printer Epson LX-310 (dot matrix)."""
        try:
            # Sesuaikan dengan port printer Anda, contoh: 'LPT1', 'COM1', '/dev/ttyUSB0'
            printer_port = "LPT1"  # Ganti dengan port printer Anda

            with open(printer_port, "w") as printer:
                # Judul
                printer.write("\033@")  # Reset printer
                printer.write("\033!8")  # Set character size (ukuran font)
                printer.write("SURAT PENERIMAAN BARANG\n")
                printer.write("\033!0") # Reset character size
                printer.write("\n")

                # Header
                printer.write(f"No. Penerimaan : {no_penerimaan}\n")
                printer.write(f"Tanggal       : {tanggal}\n")
                printer.write(f"Supplier      : {supplier}\n")
                printer.write(f"Keterangan    : {keterangan}\n")
                printer.write("\n")

                # Tabel
                printer.write("-" * 65 + "\n")
                printer.write("No. Barcode        Nama Barang             Varian      Qty\n")
                printer.write("-" * 65 + "\n")
                total_qty = 0

                # Mengambil data nama produk dan varian dari database
                conn = None
                try:
                    conn = sqlite3.connect('produk.db')
                    cursor = conn.cursor()

                    for i, barang in enumerate(detail_barang):
                        barcode, _, _, qty, _ = barang

                        # Ambil nama produk dan varian dari database
                        cursor.execute("SELECT nama_produk, nama_varian FROM produk WHERE barcode = ?", (barcode,))
                        result = cursor.fetchone()
                        if result:
                            nama_barang, varian = result
                        else:
                            nama_barang, varian = "Tidak Diketahui", "Tidak Diketahui"

                        printer.write(f"{i+1:<3} {barcode:<13} {nama_barang:<23} {varian:<11} {qty:>3}\n")
                        total_qty += int(qty)

                    printer.write("-" * 65 + "\n")
                    printer.write(f"Total Qty: {total_qty}\n")
                    printer.write("\n\n")

                    # Footer Tanda Tangan
                    printer.write("    Penerima,                  Yang Menyerahkan,\n")
                    printer.write("\n\n\n")
                    printer.write("    (           )              (           )\n")

                    messagebox.showinfo("Info", "Surat Penerimaan Barang berhasil dicetak ke Epson LX-310.")

                except Exception as e:
                    messagebox.showerror("Error", f"Terjadi kesalahan saat mencetak ke Epson LX-310: {e}")
                finally:
                    if conn:
                        conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mencetak ke printer: {e}")
            return

    def register_font(self, font_name, font_path):
        """Mendaftarkan font ke ReportLab."""
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            print(f"Font {font_name} berhasil didaftarkan.")
        except Exception as e:
            print(f"Gagal mendaftarkan font {font_name}: {e}")

    def clear_form(self):
        """Membersihkan form."""
        self.generate_no_penerimaan()
        self.tanggal.set(date.today().strftime('%Y-%m-%d'))
        self.combobox_supplier.set("")
        self.keterangan.set("")
        for row in self.tabel.get_children():
            self.tabel.delete(row)
        self.refresh_total_qty()

class TambahBarangWindow:
    def __init__(self, root, tabel, refresh_total_qty_callback):
        self.root = root
        self.tabel = tabel
        self.refresh_total_qty_callback = refresh_total_qty_callback
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

        self.listbox_suggestions = tk.Listbox(self.root, height=5, exportselection=0)
        self.listbox_suggestions.grid(row=1, column=1, padx=5, sticky="ew")
        self.listbox_suggestions.bind("<<ListboxSelect>>", self.fill_entry_from_listbox)

        ttk.Label(self.root, text="Varian Warna:", style="TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.varian_entry = ttk.Entry(self.root, textvariable=self.selected_varian, state='disabled', style='Disabled.TEntry')
        self.varian_entry.grid(row=2, column=1, padx=5, pady=5)

        # Frame untuk Listbox dan Scrollbar
        self.frame_listbox_varian = ttk.Frame(self.root)
        self.frame_listbox_varian.grid(row=3, column=1, padx=5, sticky="ew")

        # Listbox Varian dengan Scrollbar
        self.listbox_varian_suggestions = tk.Listbox(self.frame_listbox_varian, height=5, exportselection=0)
        self.listbox_varian_suggestions.pack(side="left", fill="both", expand=True)
        self.listbox_varian_suggestions.bind("<<ListboxSelect>>", self.fill_varian_entry_from_listbox)

        # Scrollbar Vertikal
        self.scrollbar_varian = ttk.Scrollbar(self.frame_listbox_varian, orient="vertical", command=self.listbox_varian_suggestions.yview)
        self.scrollbar_varian.pack(side="right", fill="y")
        self.listbox_varian_suggestions.config(yscrollcommand=self.scrollbar_varian.set)

        ttk.Label(self.root, text="QTY:", style="TLabel").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.root, textvariable=self.selected_qty, style="TEntry").grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(self.root, text="Keterangan:", style="TLabel").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.root, textvariable=self.selected_keterangan, style="TEntry").grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(self.root, text="Tambah", command=self.tambah_ke_tabel, style="success.TButton").grid(row=6, column=0, columnspan=2, pady=10)

        # Load data produk for suggestions
        self.update_nama_produk_list()
        self.selected_product.trace_add("write", self.on_nama_barang_selected)

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
            self.suggestions = []
            for item in self.nama_produk_list:
                ratio = fuzz.ratio(typed.lower(), item.lower())
                if ratio >= 60:
                    self.suggestions.append(item)

        # Batasi jumlah sugesti yang ditampilkan
        self.suggestions = self.suggestions[:5]

        self.update_listbox()
        self.listbox_suggestions.config(height=5)

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
            self.varian_produk_list = sorted([item[0] for item in cursor.fetchall()])
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
            self.selected_varian.set(selected_item)
            self.hide_varian_listbox()
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
        # Reset dan nonaktifkan entry varian saat produk berubah
        self.selected_varian.set("")

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

