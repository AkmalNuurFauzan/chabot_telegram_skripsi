import sqlite3

print("Memulai pembuatan database...")

# 1. Membuat/Membuka koneksi ke file database
# Jika file sahalnet.db belum ada, Python akan otomatis membuatnya di folder yang sama
conn = sqlite3.connect('sahalnet.db')
cursor = conn.cursor()

# 2. Membuat Tabel Pelanggan
# Kita rancang struktur kolomnya sesuai tabel visual sebelumnya
cursor.execute('''
CREATE TABLE IF NOT EXISTS pelanggan (
    id_telegram INTEGER PRIMARY KEY,
    nama TEXT,
    nik TEXT,
    alamat TEXT,
    nomor_hp TEXT,
    deadline_tagihan TEXT,
    status TEXT
)
''')

# 3. Menyiapkan Data Dummy
data_dummy = [
    (1362593335, 'Asep Sunandar', '3271012345678901', 'Jl. Pelabuhan II No. 45', '081234567890', '2026-07-15', 'Terhubung'),
    (9876543210, 'Siti Aminah', '3271023456789012', 'Jl. Suryakencana No. 12', '081345678901', '2026-07-05', 'Terputus'),
    (1122334455, 'Budi Santoso', '3271034567890123', 'Jl. Cikole Dalam No. 8', '081567890123', '2026-07-10', 'Terhubung')
]

# 4. Memasukkan Data ke dalam Tabel
# Menggunakan INSERT OR IGNORE agar data tidak ganda jika script dijalankan berkali-kali
cursor.executemany('''
INSERT OR IGNORE INTO pelanggan (id_telegram, nama, nik, alamat, nomor_hp, deadline_tagihan, status)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', data_dummy)

# 5. Menyimpan perubahan dan menutup koneksi
conn.commit()
conn.close()

print("Database 'sahalnet.db' berhasil dibuat dan data dummy telah dimasukkan!")