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
        self.style = Style(theme='cosmo')  # Pilih tema ttkbootstrap

        # --- Header Form ---
        self.frame_header = ttk.LabelFrame(self.root, text="Header", style="primary.TLabelframe")
        self.frame_header.pack(padx=10, pady=10, fill="x")

        # No Penerimaan (otomatis)
        ttk.Label(self.frame_header, text="No. Penerimaan:", style="TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.no_penerimaan = tk.StringVar()
        ttk.Label(self.frame_header, textvariable=self.no_penerimaan, style="TLabel").grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Tanggal
        ttk.Label(self.frame_header, text="Tanggal:", style="TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tanggal = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        self.entry_tanggal = DateEntry(self.frame_header, bootstyle="primary")
        self.entry_tanggal.grid(row=1, column=1, padx=5, pady=5)
        self.tanggal.set(date.today().strftime('%Y-%m-%d'))  # Set tanggal awal
        self.entry_tanggal.bind("<<DateEntrySelected>>", self.update_tanggal)

        # Supplier
        ttk.Label(self.frame_header, text="Supplier:", style="TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.supplier_id = tk.StringVar()
        self.supplier_options = self.get_supplier_options()  # Ambil data supplier dari database
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
        TambahBarangWindow(window_tambah, self.tabel, self.refresh_total_qty)

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
        """Menyimpan data penerimaan barang ke database dan mencetak PDF"""
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
            values = self.tabel.item(item, "values")
            detail_barang.append(values)

        supplier_id = int(supplier.split(" - ")[0])

        conn = None
        try:
            conn = sqlite3.connect("produk.db")
            cursor = conn.cursor()

            # Simpan data ke tabel penerimaan_barang
            cursor.execute(
                "INSERT INTO penerimaan_barang (no_penerimaan, tanggal, supplier_id, keterangan) VALUES (?, ?, ?, ?)",
                (no_penerimaan, tanggal, supplier_id, keterangan),
            )

            # Simpan data ke tabel detail_penerimaan dan update stok
            for barang in detail_barang:
                barcode = barang[0]
                qty = int(barang[3])

                cursor.execute(
                    "INSERT INTO detail_penerimaan (no_penerimaan, barcode, qty) VALUES (?, ?, ?)",
                    (no_penerimaan, barcode, qty),
                )

                # Cek apakah barang sudah ada di tabel stok
                cursor.execute("SELECT qty_stok FROM stok WHERE barcode = ?", (barcode,))
                row = cursor.fetchone()
                if row:
                    # Update stok
                    new_qty = row[0] + qty
                    cursor.execute(
                        "UPDATE stok SET qty_stok = ? WHERE barcode = ?", (new_qty, barcode)
                    )
                else:
                    # Tambah barang ke tabel stok
                    cursor.execute(
                        "INSERT INTO stok (barcode, qty_stok) VALUES (?, ?)", (barcode, qty)
                    )

            conn.commit()
            messagebox.showinfo("Info", "Data penerimaan barang berhasil disimpan!")

            # Cetak PDF
            self.cetak_pdf()

            # Clear form setelah berhasil menyimpan dan mencetak
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

    def cetak_pdf(self):
        """Membuat dan mencetak PDF surat penerimaan barang."""
        try:
            # Ambil data dari form dan tabel
            no_penerimaan = self.no_penerimaan.get()
            tanggal = self.tanggal.get()
            supplier = self.supplier_id.get()
            keterangan = self.keterangan.get()
            detail_barang = []
            for item in self.tabel.get_children():
                values = self.tabel.item(item, "values")
                detail_barang.append(values)

            # Buat PDF
            pdf_filename = f"PenerimaanBarang_{no_penerimaan}.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=letter)

            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 750, "Surat Penerimaan Barang")
            c.setFont("Helvetica", 12)
            c.drawString(50, 730, f"No. Penerimaan: {no_penerimaan}")
            c.drawString(50, 715, f"Tanggal: {tanggal}")
            c.drawString(50, 700, f"Supplier: {supplier}")
            c.drawString(50, 685, f"Keterangan: {keterangan}")

            # Tabel
            data = [["Barcode", "Nama Barang", "Varian", "QTY", "Keterangan"]]
            for barang in detail_barang:
                data.append(barang)

            # Hitung total QTY
            total_qty = sum(int(barang[3]) for barang in detail_barang)
            data.append(["", "", "Total QTY:", total_qty, ""])

            # Atur Column width dan posisi mulai tabel
            col_widths = [1.5 * inch, 2.5 * inch, 1 * inch, 0.5 * inch, 1.5 * inch]
            table_y_position = 650 - len(data) * 20
            if table_y_position < 50:
                table_y_position = 50

            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            table.wrapOn(c, 50, 800)
            table.drawOn(c, 50, table_y_position)

            # Simpan PDF
            c.save()
            messagebox.showinfo("Info", f"PDF berhasil dibuat: {pdf_filename}")

            # Buka PDF (opsional)
            import os
            os.startfile(pdf_filename)

        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuat PDF: {e}")
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
        self.nama_barang_entry.bind("<FocusIn>", lambda event: self.nama_barang_entry.event_generate('<KeyRelease>'))
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
