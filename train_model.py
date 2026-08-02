import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report, accuracy_score
import joblib

# 1. BACA DATASET
# Pastikan nama file CSV di bawah ini sesuai dengan file yang sudah kamu unduh sebelumnya
nama_file = 'Dataset_NLP_1500_Balanced_250_Fixed.csv'

print(f"Membaca dataset dari {nama_file}...")
try:
    df = pd.read_csv(nama_file)
except FileNotFoundError:
    print(f"ERROR: File {nama_file} tidak ditemukan di folder ini!")
    exit()

# Mengambil kolom yang penting
# X = Fitur (Teks Keluhan dari pelanggan)
# y = Target (Label/Kategori masalah)
X = df['Isi_Pesan']
y = df['Label_Masalah']

# 2. BAGI DATA (TRAINING & TESTING)
# Kita membagi data: 80% untuk melatih AI, 20% untuk menguji seberapa pintar AI-nya
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. BUAT DAN LATIH MODEL (PIPELINE)
print("Sedang melatih otak AI...")
# Pipeline ini akan otomatis:
# a. Mengubah kalimat (Isi_Pesan) menjadi vektor angka menggunakan TfidfVectorizer
# b. Memasukkan angka tersebut ke algoritma Logistic Regression untuk dipelajari
model = make_pipeline(
    TfidfVectorizer(lowercase=True), 
    LogisticRegression(max_iter=1000)
)

# Proses Training (Belajar)
model.fit(X_train, y_train)

# 4. EVALUASI MODEL (UJI AKURASI)
print("\n--- HASIL EVALUASI AI ---")
y_pred = model.predict(X_test)
akurasi = accuracy_score(y_test, y_pred) * 100
print(f"Akurasi Model: {akurasi:.2f}%\n")
print("Detail Laporan Klasifikasi:")
print(classification_report(y_test, y_pred))

# 7. VISUALISASI CONFUSION MATRIX
print("\nMembuat visualisasi Confusion Matrix...")

# Menghitung matriks konfusi
cm = confusion_matrix(y_test, y_pred)

# Membuat figur / kanvas grafik
plt.figure(figsize=(10, 8))

# Membuat heatmap dengan Seaborn
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=model.classes_, 
            yticklabels=model.classes_)

# Menambahkan judul dan label sumbu
plt.title('Confusion Matrix - Klasifikasi Keluhan Pelanggan Sahalnet', pad=20, fontsize=14)
plt.ylabel('Label Aktual (Sebenarnya)', fontsize=12)
plt.xlabel('Label Prediksi AI', fontsize=12)

# Merapikan layout agar label tidak terpotong
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# Menyimpan gambar otomatis ke folder project
plt.savefig('Confusion_Matrix_Sahalnet.png', dpi=300)
print("Gambar Confusion Matrix berhasil disimpan sebagai 'Confusion_Matrix_Sahalnet.png'")

# Menampilkan pop-up gambar (opsional, tutup jendela gambarnya untuk melanjutkan terminal)
plt.show()
# # 5. SIMPAN MODEL
# # Menyimpan model yang sudah pintar ke dalam file .pkl agar bisa dipakai bot telegram
nama_model_output = 'model_chatbot.pkl'
joblib.dump(model, nama_model_output)
print(f"Model berhasil disimpan sebagai '{nama_model_output}'!")

# 6. TESTER INTERAKTIF (UJI COBA LANGSUNG DI TERMINAL)
# print("\n=================================================")
# print("  UJI COBA AI (Ketik 'keluar' untuk mengakhiri)")
# print("=================================================")
# while True:
#     pesan_masuk = input("\nPelanggan: ")
    
#     if pesan_masuk.lower() == 'keluar':
#         print("Selesai. Silakan jalankan telegram_bot.py kamu!")
#         break
        
#     # AI melakukan prediksi
#     prediksi_kategori = model.predict([pesan_masuk])[0]
    
#     # Menghitung keyakinan AI (%)
#     probabilitas = max(model.predict_proba([pesan_masuk])[0]) * 100
    
#     print(f"AI Bot   : [Mendeteksi: {prediksi_kategori}] (Akurasi: {probabilitas:.1f}%)")