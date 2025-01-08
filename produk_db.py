import sqlite3
from datetime import datetime  # Tambahkan baris ini


def create_database():
    """Membuat database dan tabel jika belum ada."""
    conn = sqlite3.connect('produk.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produk (
            kode_produk TEXT,
            nama_produk TEXT,
            deskripsi TEXT,
            kode_toko TEXT,
            barcode TEXT PRIMARY KEY,
            kode_varian TEXT,
            nama_varian TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aksi TEXT,
            waktu DATETIME,
            data_lama TEXT,
            data_baru TEXT,
            keterangan TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplier (
            id_supplier INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            kategori TEXT
        )
    ''')

    # Tabel penerimaan_barang
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nomor_spb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tahun_bulan TEXT,
            nomor_terakhir INTEGER
        )
    ''')

    # Tabel detail_penerimaan
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detail_penerimaan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no_penerimaan TEXT,
            barcode TEXT,
            qty INTEGER,
            FOREIGN KEY (no_penerimaan) REFERENCES penerimaan_barang(no_penerimaan),
            FOREIGN KEY (barcode) REFERENCES produk(barcode)
        )
    ''')

    # Tabel stok
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stok (
            barcode TEXT PRIMARY KEY,
            qty_stok INTEGER,
            FOREIGN KEY (barcode) REFERENCES produk(barcode)
        )
    ''')

    conn.commit()
    conn.close()

# Panggil fungsi ini untuk membuat database saat aplikasi pertama kali dijalankan
# create_database()

def tambah_produk(kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian):
    """Menambahkan data produk ke database."""
    conn = sqlite3.connect('produk.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO produk (kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian))

    conn.commit()
    conn.close()

    # Catat log setelah penambahan produk
    catat_log('TAMBAH PRODUK', None, str((kode_produk, nama_produk, deskripsi, kode_toko, barcode, kode_varian, nama_varian)), 'Penambahan produk baru')


def ambil_semua_produk():
    """Mengambil semua data produk dari database."""
    conn = sqlite3.connect('produk.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produk")
    rows = cursor.fetchall()

    conn.close()
    return rows

def ambil_produk_berdasarkan_nama_dan_varian(nama_produk, nama_varian):
    """Mengambil data produk berdasarkan nama produk dan nama varian."""
    conn = sqlite3.connect('produk.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produk WHERE nama_produk = ? AND nama_varian = ?", (nama_produk, nama_varian))
    row = cursor.fetchone()
    conn.close()
    return row

def catat_log(aksi, data_lama, data_baru, keterangan):
    """Mencatat log perubahan data ke tabel log_produk."""
    conn = sqlite3.connect('produk.db')
    cursor = conn.cursor()

    waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO log_produk (aksi, waktu, data_lama, data_baru, keterangan)
        VALUES (?, ?, ?, ?, ?)
    ''', (aksi, waktu, str(data_lama), str(data_baru), keterangan))

    conn.commit()
    conn.close()

def ambil_semua_supplier():
    """Mengambil semua data supplier dari database."""
    conn = sqlite3.connect('produk.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM supplier")
    rows = cursor.fetchall()
    conn.close()
    return rows


