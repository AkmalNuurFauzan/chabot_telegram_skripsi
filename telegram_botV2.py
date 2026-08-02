import telebot
import joblib
import os
import whisper
import sqlite3
from datetime import datetime
from pydub import AudioSegment
from pydub.effects import normalize
from deep_translator import GoogleTranslator

# ==========================================
# FUNGSI CEK DATABASE TERBARU
# ==========================================
def cari_id_pelanggan(nama, nik):
    """
    Fungsi ini menarik data lalu dicocokkan menggunakan logika Python.
    Pencocokan hanya menggunakan Nama dan NIK.
    """
    conn = sqlite3.connect('sahalnet.db')
    cursor = conn.cursor()
    
    # Cukup ambil 3 kolom ini saja karena alamat sudah tidak dipakai untuk verifikasi
    cursor.execute("SELECT id_pelanggan, nama, nik FROM pelanggan")
    semua_data = cursor.fetchall()
    conn.close() 

    # Bersihkan input dari Telegram 
    nama_input = str(nama).strip().lower()
    nik_input = str(nik).strip()
    
    print(f"\n[DEBUG LOGIN] Mencari -> Nama: '{nama_input}', NIK: '{nik_input}'")

    # Cocokkan satu per satu menggunakan Python
    for baris in semua_data:
        db_id = baris[0]
        db_nama = str(baris[1]).strip().lower()
        db_nik = str(baris[2]).strip()

        # Cek apakah Nama dan NIK cocok
        if db_nama == nama_input and db_nik == nik_input:
            print(f"[DEBUG LOGIN] ✅ KETEMU! Login sukses untuk ID: {db_id}")
            return {"id_pelanggan": db_id, "nama_asli": baris[1]}

    print("[DEBUG LOGIN] ❌ GAGAL! Tidak ada data yang cocok.")
    return None

def ambil_data_pelanggan_by_id(id_pelanggan):
    """
    Fungsi ini mengambil seluruh data pelanggan menggunakan id_pelanggan (PLID-XXXX)
    """
    conn = sqlite3.connect('sahalnet.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nama, alamat, deadline_tagihan, status, nik, nomor_hp FROM pelanggan WHERE id_pelanggan = ?", (id_pelanggan,))
    hasil = cursor.fetchone() 
    conn.close() 
    
    if hasil:
        return {
            "nama": hasil[0],
            "alamat": hasil[1],
            "deadline_tagihan": hasil[2],
            "status": hasil[3],
            "nik": hasil[4],       
            "nomor_hp": hasil[5]   
        }
    return None

# ==========================================
# 1. KONFIGURASI TOKEN TELEGRAM
# ==========================================
TOKEN_TELEGRAM = '8822365196:AAGkm1D5iuC1bsOb1Yqfy9RlhLDexGUQtNM'
bot = telebot.TeleBot(TOKEN_TELEGRAM)

# ==========================================
# 2. MUAT OTAK AI (NLP & WHISPER)
# ==========================================
print("Memuat otak AI NLP...")
try:
    model = joblib.load('model_chatbot.pkl')
    print("Otak AI NLP berhasil dimuat!")
except Exception as e:
    print("Gagal memuat model. Pastikan train_model.py sudah dijalankan.")
    exit()

print("Memuat model Whisper Gratis (Base)...")
whisper_model = whisper.load_model("base")
print("Model Whisper siap digunakan!")

# ==========================================
# 3. BANK JAWABAN (TEMPLATE)
# ==========================================
jawaban_template = {
    'Ganti Password': 'Bisa Kak! Silakan ketik nama WiFi dan password baru yang diinginkan di chat ini ya.',
    'Belum Bayar Tagihan': 'Mohon maaf Kak, layanan sedang dibekukan karena ada tagihan bulanan yang belum terbayar. Silakan selesaikan pembayaran terlebih dahulu ya.',
    'Gangguan Pusat': 'Terima kasih laporannya Kak. Sistem kami mendeteksi ada gangguan jaringan/kabel di area Kakak. Tim teknisi sudah kami jadwalkan untuk perbaikan/penyambungan ulang di lokasi.',
    'Wifi Lemot': 'Maaf atas ketidaknyamanannya, Kak. Kami bantu optimasi jaringan dari pusat sekarang. Coba juga restart routernya ya.',
    'Router Error': 'Halo Kak, sistem mendeteksi ada error pada router (bisa dari adaptor, kabel power, atau perangkat itu sendiri). Coba cabut-colok adaptornya dulu ya biar ke-refresh. Jika masih mati total atau lampu tetap bermasalah, teknisi kami akan datang membawa unit/adaptor pengganti.',
    'Internet Mati (LOS)': 'Wah, indikator merah (LOS) menandakan koneksi ke rumah Kakak terputus. Laporan sudah kami catat dan teknisi segera meluncur untuk pengecekan.'
}

# ==========================================
# 4. MANAJEMEN SESI PELANGGAN
# ==========================================
user_sessions = {}

def get_session(user_id):
    if user_id not in user_sessions:
        # Variabel penampung alamat sudah dihapus
        user_sessions[user_id] = {
            'state': 'NEW', 
            'attempts': 0,
            'temp_nama': '',
            'temp_nik': '',
            'id_pelanggan': None
        }
    return user_sessions[user_id]

def reset_session(user_id):
    if user_id in user_sessions:
        del user_sessions[user_id]

# ==========================================
# 5. LOGIKA PERCAKAPAN CHATBOT
# ==========================================
def proses_alur_percakapan(message, pesan_teks):
    user_id = message.chat.id
    print(f"[LOG] Pesan dari ID Telegram: {user_id} | Teks: {pesan_teks}")

    session = get_session(user_id)
    state = session['state']
    
    # Restart alur jika user mengetik /start
    if pesan_teks.lower() == '/start':
        reset_session(user_id)
        session = get_session(user_id)
        bot.reply_to(message, "Halo! Selamat datang di layanan asisten virtual *Sahalnet*.\n\nUntuk keamanan data, mari kita lakukan verifikasi terlebih dahulu ya.\n\nSilakan ketik *Nama Lengkap* Kakak sesuai data pendaftaran:", parse_mode='Markdown')
        session['state'] = 'WAITING_NAMA'
        return

    # --- ALUR VERIFIKASI (LOGIN) ---
    # --- ALUR VERIFIKASI (LOGIN) ---
    if state == 'NEW':
        bot.reply_to(message, "Halo! Selamat datang di layanan asisten virtual *Sahalnet*.\n\nUntuk keamanan data, mari kita lakukan verifikasi terlebih dahulu ya.\n\nSilakan ketik *Nama Lengkap* Kakak sesuai data pendaftaran:", parse_mode='Markdown')
        session['state'] = 'WAITING_NAMA'
        
    elif state == 'WAITING_NAMA':
        session['temp_nama'] = pesan_teks.strip()
        bot.reply_to(message, "Baik. Selanjutnya, mohon ketikkan 16 digit *NIK* (Nomor Induk Kependudukan) Kakak:", parse_mode='Markdown')
        session['state'] = 'WAITING_NIK'
        
    elif state == 'WAITING_NIK':
        session['temp_nik'] = pesan_teks.strip()
        bot.reply_to(message, "⏳ *Sedang memverifikasi data Kakak di sistem...*", parse_mode='Markdown')
        
        # Eksekusi pencarian HANYA menggunakan Nama dan NIK
        hasil_verifikasi = cari_id_pelanggan(session['temp_nama'], session['temp_nik'])
        
        if hasil_verifikasi:
            # Login Berhasil!
            session['id_pelanggan'] = hasil_verifikasi['id_pelanggan']
            nama_asli = hasil_verifikasi['nama_asli']
            
            bot.reply_to(message, f"✅ *Verifikasi Berhasil!*\n\nHalo Kak *{nama_asli}*! Senang bisa melayani Kakak. Ada kendala internet apa yang bisa kami bantu hari ini?\n\n*(Kakak bisa mengetik keluhan atau mengirimkan Voice Note/Suara)*", parse_mode='Markdown')
            session['state'] = 'WAITING_PROBLEM'
        else:
            # Login Gagal
            reset_session(user_id)
            bot.reply_to(message, "❌ *Mohon maaf Kak, kombinasi Nama dan NIK tidak ditemukan di database kami.*\n\nSilakan pastikan tidak ada salah ketik (typo). Ketik `/start` untuk mengulangi proses verifikasi.", parse_mode='Markdown')

    # --- ALUR PENANGANAN KELUHAN (SETELAH LOGIN) ---
    elif state == 'WAITING_PROBLEM':
        # Translate HANYA dilakukan pada saat user melaporkan keluhan
        try:
            pesan_indo = GoogleTranslator(source='auto', target='id').translate(pesan_teks)
        except Exception as e:
            print(f"[SISTEM] Gagal menerjemahkan: {e}")
            pesan_indo = pesan_teks
            
        pesan_indo_lower = pesan_indo.lower()
        
        # NLP Prediksi
        prediksi_kategori = model.predict([pesan_indo])[0]
        akurasi = max(model.predict_proba([pesan_indo])[0]) * 100
        
        session['last_problem_category'] = prediksi_kategori
        session['last_user_message'] = pesan_teks
        
        print(f"\n[AI-LOG] ID Pelanggan (DB): {session['id_pelanggan']}")
        print(f"[AI-LOG] Keluhan Asli     : {pesan_teks}")
        print(f"[AI-LOG] Prediksi Kategori: {prediksi_kategori} (Keyakinan: {akurasi:.1f}%)")
        
        # Tarik data lengkap untuk mengecek status tagihan
        data_user = ambil_data_pelanggan_by_id(session['id_pelanggan'])
        is_menunggak = False 
        
        if data_user and data_user['status'] == 'terputus':
            try:
                deadline_date = datetime.strptime(data_user['deadline_tagihan'], "%Y-%m-%d").date()
                hari_ini = datetime.now().date()
                if hari_ini > deadline_date:
                    is_menunggak = True
            except ValueError:
                is_menunggak = True 

        # Skenario 1: Override Tagihan
        if is_menunggak:
            balasan = (
                f"Mohon maaf Kak *{data_user['nama']}*, setelah dilakukan pengecekan sistem, "
                f"layanan internet di *{data_user['alamat']}* saat ini sedang dinonaktifkan sementara "
                f"karena telah melewati batas tanggal pembayaran (*{data_user['deadline_tagihan']}*). "
                f"Silakan selesaikan pembayaran terlebih dahulu agar internet Kakak otomatis aktif kembali ya."
            )
            session['last_problem_category'] = 'Belum Bayar Tagihan'
        
        # Skenario 2: Keluhan Normal
        else:
            balasan = jawaban_template.get(prediksi_kategori, "Maaf Kak, keluhan belum bisa dipahami secara spesifik.")
        
        teks_kirim = f"{balasan}\n\n*Apakah panduan atau informasi ini sudah membantu mengatasi kendala Kakak? (Balas: Sudah / Belum)*"
        bot.reply_to(message, teks_kirim, parse_mode='Markdown')
        
        session['state'] = 'CHECK_RESOLVED'
        session['attempts'] += 1
        
    elif state == 'CHECK_RESOLVED':
        pesan_indo_lower = pesan_teks.lower()
        kata_positif = ['sudah', 'ya', 'mantap', 'bisa', 'oke', 'berhasil', 'terbantu', 'baik']
        
        if any(kata in pesan_indo_lower for kata in kata_positif):
            bot.reply_to(message, "Alhamdulillah! Terima kasih banyak atas laporannya ya Kak. 🙏\n\nApakah Kakak ingin mengakhiri sesi obrolan ini atau ada kendala lain? *(Balas: Akhiri / Lanjut)*", parse_mode='Markdown')
            session['state'] = 'ASK_END'
        else:
            if session['attempts'] >= 3:
                kategori_kendala = session.get('last_problem_category', 'Kendala Tidak Diketahui')
                pesan_pengguna = session.get('last_user_message', '-')
                
                # Tarik data tiket menggunakan ID Pelanggan yang sudah terlogin
                data_tiket = ambil_data_pelanggan_by_id(session['id_pelanggan'])
                
                if data_tiket:
                    teks_teknisi = (
                        f"Mohon maaf Kak jika panduan kami belum berhasil mengatasi masalahnya. 😔\n\n"
                        f"Sebagai tindak lanjut, laporan Kakak telah kami teruskan langsung ke *Tim Teknisi* dengan detail tiket berikut:\n\n"
                        f"🎫 *TIKET PELAPORAN GANGGUAN*\n"
                        f"▪️ *ID Pelanggan:* `{session['id_pelanggan']}`\n"
                        f"▪️ *Nama:* {data_tiket['nama']}\n"
                        f"▪️ *NIK:* {data_tiket['nik']}\n"
                        f"▪️ *No. HP:* {data_tiket['nomor_hp']}\n"
                        f"▪️ *Alamat:* {data_tiket['alamat']}\n\n"
                        f"📝 *DETAIL KENDALA*\n"
                        f"▪️ *Kategori Sistem:* {kategori_kendala}\n"
                        f"▪️ *Pesan Keluhan:* \"{pesan_pengguna}\"\n\n"
                        f"Tim teknisi kami akan segera menghubungi nomor HP terdaftar dan meluncur ke lokasi. Terima kasih banyak atas kesabarannya ya Kak! 🙏\n\n"
                        f"*(Sesi laporan otomatis ditutup)*"
                    )
                else:
                    teks_teknisi = "Laporan telah diteruskan ke teknisi."
                
                bot.reply_to(message, teks_teknisi, parse_mode='Markdown')
                reset_session(user_id)
            else:
                sisa_percobaan = 3 - session['attempts']
                bot.reply_to(message, f"Mohon maaf Kak kalau belum berhasil. Boleh dijelaskan lebih detail lagi kendalanya seperti apa? Kakak bisa kirim Voice Note juga biar lebih mudah.\n\n*(Sisa percobaan bantuan otomatis: {sisa_percobaan}x)*")
                session['state'] = 'WAITING_PROBLEM'

    elif state == 'ASK_END':
        pesan_indo_lower = pesan_teks.lower()
        kata_selesai = ['akhiri', 'selesai', 'tutup', 'tidak', 'udah', 'cukup']
        
        if any(kata in pesan_indo_lower for kata in kata_selesai):
            bot.reply_to(message, "Baik Kak, terima kasih telah menggunakan layanan Sahalnet. Semoga internetnya lancar terus! Sesi percakapan ini telah ditutup. 👋")
            reset_session(user_id)
        else:
            bot.reply_to(message, "Siap Kak! Silakan ceritakan kembali kendala lain yang sedang dialami.")
            session['state'] = 'WAITING_PROBLEM'
            session['attempts'] = 0

# ==========================================
# 6. ROUTING PESAN DARI TELEGRAM (TEKS & SUARA)
# ==========================================

@bot.message_handler(content_types=['text'])
def respon_teks(message):
    proses_alur_percakapan(message, message.text)

@bot.message_handler(content_types=['voice', 'audio'])
def respon_suara(message):
    file_path_ogg = f"temp_voice_{message.chat.id}.ogg"
    file_path_wav = f"temp_voice_{message.chat.id}.wav"
    
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(file_path_ogg, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        audio = AudioSegment.from_file(file_path_ogg, format="ogg")
        normalized_audio = normalize(audio)
        normalized_audio.export(file_path_wav, format="wav")
            
        transcription = whisper_model.transcribe(
            file_path_wav, 
            language="id", 
            fp16=False,
            temperature=0.0
        )
        teks_hasil_whisper = transcription["text"]
        proses_alur_percakapan(message, teks_hasil_whisper)
        
    except Exception as e:
        print(f"[ERROR SUARA] {e}")
        bot.reply_to(message, "Maaf Kak, terjadi kendala teknis saat memproses suara. Boleh tolong diketik saja?")
        
    finally:
        if os.path.exists(file_path_ogg):
            os.remove(file_path_ogg)
        if os.path.exists(file_path_wav):
            os.remove(file_path_wav)

# ==========================================
# JALANKAN BOT
# ==========================================
print("\n=========================================================")
print(" Bot Telegram Sahalnet Berjalan (Alur Verifikasi Aktif) ")
print("=========================================================\n")
bot.infinity_polling()