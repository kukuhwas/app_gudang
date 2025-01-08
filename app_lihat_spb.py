import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from ttkbootstrap import Style, DateEntry
from datetime import date
from fuzzywuzzy import fuzz, process
from produk_db import catat_log, ambil_semua_supplier # Pastikan import database sudah benar
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import webbrowser

class WindowLihatSPB:
    def __init__(self, root):
        self.root = root
        self.root.title("Lihat Surat Penerimaan Barang")
        self.root.geometry("1100x600")

        # --- Variabel ---
        self.current_page = 1
        self.data_per_page = 20
        self.total_data = 0
        self.selected_spb_id = None

        self.search_term = tk.StringVar()
        self.filter_tanggal = tk.StringVar()
        self.filter_supplier = tk.StringVar(value="Semua")
        self.sort_by = tk.StringVar(value="tanggal_desc")

        # --- Style ---
        self.style = Style(theme='cosmo')

        # --- Frame Pencarian ---
        frame_pencarian = tk.LabelFrame(self.root, text="Pencarian")
        frame_pencarian.pack(padx=10, pady=10, fill="x")

        tk.Label(frame_pencarian, text="Nama Produk:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(frame_pencarian, textvariable=self.search_term).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Button(frame_pencarian, text="Cari", command=self.cari_data).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(frame_pencarian, text="Clear", command=self.clear_search).grid(row=0, column=3, padx=5, pady=5)

        # --- Frame Filter ---
        frame_filter = tk.LabelFrame(self.root, text="Filter")
        frame_filter.pack(padx=10, pady=5, fill="x")

        tk.Label(frame_filter, text="Tanggal:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_tanggal = DateEntry(frame_filter, bootstyle="primary")
        self.entry_tanggal.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.entry_tanggal.bind("<<DateEntrySelected>>", self.update_tanggal)

        tk.Label(frame_filter, text="Supplier:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.supplier_options = ["Semua"] + self.get_supplier_options()
        self.combobox_supplier = ttk.Combobox(frame_filter, textvariable=self.filter_supplier, values=self.supplier_options, state="readonly", style="primary.TCombobox")
        self.combobox_supplier.current(0)
        self.combobox_supplier.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.combobox_supplier.bind("<<ComboboxSelected>>", self.filter_data)

        # --- Frame Sorting ---
        frame_sort = tk.LabelFrame(self.root, text="Urutkan")
        frame_sort.pack(padx=10, pady=5, fill="x")

        tk.Radiobutton(frame_sort, text="Tanggal Terbaru", variable=self.sort_by, value="tanggal_desc", command=self.refresh_data).pack(side="left", padx=5)
        tk.Radiobutton(frame_sort, text="Tanggal Terlama", variable=self.sort_by, value="tanggal_asc", command=self.refresh_data).pack(side="left", padx=5)
        tk.Radiobutton(frame_sort, text="No. SPB (A-Z)", variable=self.sort_by, value="no_spb_asc", command=self.refresh_data).pack(side="left", padx=5)
        tk.Radiobutton(frame_sort, text="No. SPB (Z-A)", variable=self.sort_by, value="no_spb_desc", command=self.refresh_data).pack(side="left", padx=5)

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

        # --- Tombol Cetak Ulang ---
        frame_cetak_ulang = tk.Frame(self.root)
        frame_cetak_ulang.pack(pady=5)
        self.btn_cetak_ulang = tk.Button(frame_cetak_ulang, text="Cetak Ulang SPB", command=self.cetak_ulang_spb, state="disabled")
        self.btn_cetak_ulang.pack(padx=5)

        # --- Load Data Awal ---
        self.refresh_data()

    def buat_tabel(self):
        """Membuat tabel untuk menampilkan daftar SPB."""
        self.tabel = ttk.Treeview(self.frame_tabel, columns=("no_penerimaan", "tanggal", "supplier", "keterangan"), show="headings")
        self.tabel.pack(fill="both", expand=True)

        self.tabel.heading("no_penerimaan", text="No. SPB")
        self.tabel.heading("tanggal", text="Tanggal")
        self.tabel.heading("supplier", text="Supplier")
        self.tabel.heading("keterangan", text="Keterangan")

        self.tabel.column("no_penerimaan", width=150)
        self.tabel.column("tanggal", width=100)
        self.tabel.column("supplier", width=200)
        self.tabel.column("keterangan", width=250)

        yscrollbar = ttk.Scrollbar(self.frame_tabel, orient="vertical", command=self.tabel.yview)
        yscrollbar.pack(side="right", fill="y")
        self.tabel.configure(yscrollcommand=yscrollbar.set)

        # Event binding untuk detail SPB
        self.tabel.bind("<<TreeviewSelect>>", self.show_detail_spb)

    def get_supplier_options(self):
        """Mengambil data supplier dari database."""
        suppliers = ambil_semua_supplier()
        return [f"{sup[0]} - {sup[1]}" for sup in suppliers]

    def refresh_data(self):
        """Mengambil data SPB dari database dan memperbarui tabel."""
        conn = None
        try:
            conn = sqlite3.connect('produk.db')
            cursor = conn.cursor()

            # Filter dan Cari
            query = "SELECT pb.no_penerimaan, pb.tanggal, s.nama, pb.keterangan, s.id_supplier FROM penerimaan_barang pb JOIN supplier s ON pb.supplier_id = s.id_supplier WHERE 1=1"
            params = []

            # Filter tanggal
            if self.filter_tanggal.get():
              tanggal = self.filter_tanggal.get()
              query += " AND DATE(pb.tanggal) = ?"
              params.append(tanggal)

            # Filter supplier
            if self.filter_supplier.get() != "Semua":
              supplier_id = int(self.filter_supplier.get().split(" - ")[0])
              query += " AND pb.supplier_id = ?"
              params.append(supplier_id)

            # Pencarian
            search_term = self.search_term.get().lower()
            if search_term:
                # Cari produk yang ada di dalam SPB
                query = f"""
                    SELECT pb.no_penerimaan, pb.tanggal, s.nama, pb.keterangan, s.id_supplier
                    FROM penerimaan_barang pb
                    JOIN supplier s ON pb.supplier_id = s.id_supplier
                    JOIN detail_penerimaan dp ON pb.no_penerimaan = dp.no_penerimaan
                    JOIN produk p ON dp.barcode = p.barcode
                    WHERE 1=1
                    AND DATE(pb.tanggal) = ?
                    AND s.nama LIKE '%{self.filter_supplier.get().split(" - ")[0]}%'
                    AND p.nama_produk LIKE '%{search_term}%'
                """
                
                # Validasi tanggal
                try:
                    tanggal = self.filter_tanggal.get()
                    date.fromisoformat(tanggal)  # Coba konversi ke date untuk validasi
                except ValueError:
                    messagebox.showerror("Error", "Format tanggal tidak valid. Gunakan frmt YYYY-MM-DD.")
                    return

                if self.filter_supplier.get() == "Semua":
                  query = f"""
                    SELECT pb.no_penerimaan, pb.tanggal, s.nama, pb.keterangan, s.id_supplier
                    FROM penerimaan_barang pb
                    JOIN supplier s ON pb.supplier_id = s.id_supplier
                    JOIN detail_penerimaan dp ON pb.no_penerimaan = dp.no_penerimaan
                    JOIN produk p ON dp.barcode = p.barcode
                    WHERE 1=1
                    AND DATE(pb.tanggal) = ?
                    AND p.nama_produk LIKE '%{search_term}%'
                  """

                params = [tanggal]

            # Sorting
            if self.sort_by.get() == "tanggal_desc":
                query += " ORDER BY pb.tanggal DESC"
            elif self.sort_by.get() == "tanggal_asc":
                query += " ORDER BY pb.tanggal ASC"
            elif self.sort_by.get() == "no_spb_asc":
                query += " ORDER BY pb.no_penerimaan ASC"
            elif self.sort_by.get() == "no_spb_desc":
                query += " ORDER BY pb.no_penerimaan DESC"

            # Pagination
            cursor.execute(query, params)
            self.total_data = len(cursor.fetchall())  # Hitung total data setelah filter dan pencarian
            query += " LIMIT ?, ?"
            params.extend([(self.current_page - 1) * self.data_per_page, self.data_per_page])

            cursor.execute(query, params)
            data_spb = cursor.fetchall()

            # Update Tabel
            for row in self.tabel.get_children():
                self.tabel.delete(row)
            for data in data_spb:
                self.tabel.insert("", tk.END, values=data[:-1]) # jangan tampilkan id_supplier

            # Update Status Bar
            self.update_status_bar()

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        finally:
            if conn:
                conn.close()

        self.update_pagination_buttons()

    def cari_data(self):
        """Memulai pencarian data berdasarkan nama produk."""
        self.current_page = 1
        self.refresh_data()

    def clear_search(self):
        """Membersihkan field pencarian."""
        self.search_term.set("")
        self.current_page = 1
        self.refresh_data()

    def filter_data(self, *args):
        """Memfilter data berdasarkan tanggal dan supplier."""
        self.current_page = 1
        self.refresh_data()

    def update_tanggal(self, event):
        """Update variabel tanggal dengan tanggal yang dipilih."""
        self.filter_tanggal.set(self.entry_tanggal.get_date().strftime('%Y-%m-%d'))
        self.filter_data()

    def update_status_bar(self):
        """Mengupdate text di status bar"""
        self.status_bar.config(text=f"Menampilkan {len(self.tabel.get_children())} dari {self.total_data} SPB")

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

    def show_detail_spb(self, event):
        """Menampilkan detail SPB yang dipilih di window baru."""
        selected_items = self.tabel.selection()
        if not selected_items:
            self.btn_cetak_ulang.config(state="disabled")
            return
        
        selected_item = selected_items[0]
        self.selected_spb_id = self.tabel.item(selected_item)['values'][0]  # Ambil No. SPB
        self.btn_cetak_ulang.config(state="normal")
        
        # Ambil data dari database
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM penerimaan_barang WHERE no_penerimaan = ?", (self.selected_spb_id,))
        spb_data = cursor.fetchone()

        # Ambil data supplier
        cursor.execute("SELECT * FROM supplier WHERE id_supplier = ?", (spb_data[2],))
        supplier_data = cursor.fetchone()

        # Ambil detail barang
        cursor.execute("SELECT p.barcode, p.nama_produk, p.nama_varian, dp.qty FROM detail_penerimaan dp JOIN produk p ON dp.barcode = p.barcode WHERE dp.no_penerimaan = ?", (self.selected_spb_id,))
        detail_barang = cursor.fetchall()

        conn.close()

        # Buat window detail
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Detail SPB - {self.selected_spb_id}")

        # Tampilkan informasi SPB
        tk.Label(detail_window, text=f"No. SPB: {spb_data[0]}", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Label(detail_window, text=f"Tanggal: {spb_data[1]}", font=('Helvetica', 10, 'bold')).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        tk.Label(detail_window, text=f"Supplier: {supplier_data[1]}", font=('Helvetica', 10, 'bold')).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        tk.Label(detail_window, text=f"Keterangan: {spb_data[3]}", font=('Helvetica', 10, 'bold')).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        
        # Membuat dan mengisi tabel detail barang
        detail_tabel = ttk.Treeview(detail_window, columns=("barcode", "nama_produk", "varian", "qty"), show="headings")
        detail_tabel.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")

        detail_tabel.heading("barcode", text="Barcode")
        detail_tabel.heading("nama_produk", text="Nama Produk")
        detail_tabel.heading("varian", text="Varian")
        detail_tabel.heading("qty", text="QTY")

        detail_tabel.column("barcode", width=150)
        detail_tabel.column("nama_produk", width=200)
        detail_tabel.column("varian", width=150)
        detail_tabel.column("qty", width=50)

        for barang in detail_barang:
            detail_tabel.insert("", tk.END, values=barang)

        # Menambahkan scrollbar ke tabel
        yscrollbar = ttk.Scrollbar(detail_window, orient="vertical", command=detail_tabel.yview)
        yscrollbar.grid(row=4, column=1, sticky="ns")
        detail_tabel.configure(yscrollcommand=yscrollbar.set)

        # Menambahkan tombol cetak ulang di window detail
        tk.Button(detail_window, text="Cetak Ulang SPB", command=lambda: self.cetak_ulang_spb(self.selected_spb_id)).grid(row=5, column=0, pady=10)

        # Konfigurasi agar row dengan tabel mengisi ruang yang tersedia
        detail_window.grid_rowconfigure(4, weight=1)
        detail_window.grid_columnconfigure(0, weight=1)

    def cetak_ulang_spb(self, no_spb=None):
        """Mencetak ulang SPB yang dipilih."""

        # Jika no_spb tidak diberikan (misalnya, dari tombol di tabel utama)
        if not no_spb:
            selected_items = self.tabel.selection()
            if not selected_items:
                messagebox.showwarning("Peringatan", "Pilih SPB yang akan dicetak ulang.")
                return
            selected_item = selected_items[0]
            no_spb = self.tabel.item(selected_item)['values'][0]

        # Ambil data SPB dari database
        conn = sqlite3.connect('produk.db')
        cursor = conn.cursor()

        try:
            # Ambil data header SPB
            cursor.execute("SELECT * FROM penerimaan_barang WHERE no_penerimaan = ?", (no_spb,))
            spb_data = cursor.fetchone()
            if not spb_data:
                messagebox.showerror("Error", f"SPB dengan nomor {no_spb} tidak ditemukan.")
                return

            # Ambil data supplier
            cursor.execute("SELECT nama FROM supplier WHERE id_supplier = ?", (spb_data[2],))
            supplier_nama = cursor.fetchone()[0]

            # Ambil detail barang
            cursor.execute("SELECT p.barcode, p.nama_produk, p.nama_varian, dp.qty FROM detail_penerimaan dp JOIN produk p ON dp.barcode = p.barcode WHERE dp.no_penerimaan = ?", (no_spb,))
            detail_barang = cursor.fetchall()

            # Cetak SPB
            self.cetak_surat_penerimaan(spb_data[0], spb_data[1], supplier_nama, spb_data[3], detail_barang, True)

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat mencetak ulang SPB: {e}")
        finally:
            conn.close()

    def cetak_surat_penerimaan(self, no_penerimaan, tanggal, supplier, keterangan, detail_barang, cetak_ulang=False):
        """Menampilkan dialog untuk memilih jenis printer dan mencetak surat penerimaan barang."""
        # Buat dialog baru hanya jika bukan cetak ulang
        if not cetak_ulang:
            dialog = tk.Toplevel(self.root)
            dialog.title("Cetak Surat Penerimaan Barang")

            # Buat radio button untuk memilih jenis printer
            printer_type = tk.StringVar(value="pdf")  # Default ke PDF
            tk.Radiobutton(dialog, text="PDF", variable=printer_type, value="pdf").pack(pady=5)
            tk.Radiobutton(dialog, text="Epson LX-310 (Dot Matrix)", variable=printer_type, value="epson").pack(pady=5)

            # Tombol Cetak
            def cetak():
                selected_printer = printer_type.get()
                dialog.destroy()  # Tutup dialog
                if selected_printer == "pdf":
                    self.cetak_pdf(no_penerimaan, tanggal, supplier, keterangan, detail_barang)
                elif selected_printer == "epson":
                    self.cetak_epson_lx310(no_penerimaan, tanggal, supplier, keterangan, detail_barang)

            tk.Button(dialog, text="Cetak", command=cetak).pack(pady=10)
        else:
            # Langsung cetak ke PDF jika cetak ulang
            self.cetak_pdf(no_penerimaan, tanggal, supplier, keterangan, detail_barang)

        # Fungsi untuk Konfigurasi Font
        def register_font(font_name, font_path):
            """Mendaftarkan font ke ReportLab."""
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                print(f"Font {font_name} berhasil didaftarkan.")
            except Exception as e:
                print(f"Gagal mendaftarkan font {font_name}: {e}")

        # Konfigurasi Font di Awal Program
        register_font('Consolas', 'fonts/Consolas.ttf')
        register_font('Consolas-Bold', 'fonts/consolab.ttf')

    def cetak_pdf(self, no_penerimaan, tanggal, supplier, keterangan, detail_barang):
        """Membuat dan mencetak surat penerimaan barang dalam format PDF."""
        file_path = f"Surat_Penerimaan_{no_penerimaan}.pdf"

        # Mendapatkan direktori saat ini
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Path lengkap ke file font
        font_path = os.path.join(current_dir, "fonts/Consolas.ttf")
        font_bold_path = os.path.join(current_dir, "fonts/consolab.ttf")

        # Mendaftarkan font
        pdfmetrics.registerFont(TTFont('Consolas', font_path))
        pdfmetrics.registerFont(TTFont('Consolas-Bold', font_bold_path))

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

        for i, barang in enumerate(detail_barang):
            barcode, nama_barang, varian, qty = barang

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

                for i, barang in enumerate(detail_barang):
                    barcode, nama_barang, varian, qty = barang

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
            messagebox.showerror("Error", f"Gagal mencetak ke printer: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    aplikasi = WindowLihatSPB(root)
    root.mainloop()
