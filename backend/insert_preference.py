import random
from sqlalchemy.orm import Session
from database import SessionLocal
from model.dosen_model import Dosen
from model.preference_model import Preference
from model.timeslot_model import TimeSlot

def generate_preferences():
    session = SessionLocal()
    try:
        # Ambil semua dosen dan timeslot yang tersedia
        dosens = session.query(Dosen).all()
        timeslots = session.query(TimeSlot).all()

        if not timeslots:
            raise ValueError("Tidak ada timeslot yang tersedia.")

        print(f"📌 Ditemukan {len(dosens)} dosen dan {len(timeslots)} timeslot.")

        # Buat dictionary untuk melacak jumlah dosen yang memilih tiap timeslot
        penggunaan_timeslot = {timeslot.id: 0 for timeslot in timeslots}

        preferences = []
        for dosen in dosens:
            jumlah_preferensi = random.randint(1, 5)  # Setiap dosen memilih 1-5 preferensi
            timeslot_terpilih = random.sample(timeslots, jumlah_preferensi)  # Pilih timeslot secara acak

            for timeslot in timeslot_terpilih:
                # Batasi jumlah dosen dalam satu timeslot (misal: max 5 dosen per timeslot)
                if penggunaan_timeslot[timeslot.id] < 5:
                    # **Hanya dosen dengan prioritas tinggi yang bisa punya alasan**
                    prioritas_tinggi = random.choices([False, True], weights=[70, 30], k=1)[0]  # 30% True
                    kebutuhan_khusus = random.choices([False, True], weights=[80, 20], k=1)[0]  # 20% True

                    alasan = None
                    if prioritas_tinggi:
                      alasan = random.choice([
    "Jadwal bentrok",
    "Tanggung jawab lain",
    "Kesehatan",
    "Jadwal luar kampus",
    "Bimbingan skripsi",
    "Beban kerja tinggi",
    "Hanya bisa di slot ini"
])


                    # **Jika prioritas_tinggi = False, alasan harus None**
                    preference = Preference(
                        dosen_id=dosen.pegawai_id,
                        timeslot_id=timeslot.id,
                        is_special_needs=kebutuhan_khusus,
                        is_high_priority=prioritas_tinggi,
                        reason=alasan  # ✅ Jika is_high_priority=False, reason tetap None
                    )
                    preferences.append(preference)
                    penggunaan_timeslot[timeslot.id] += 1

        # Masukkan preferensi ke dalam database
        session.bulk_save_objects(preferences)
        session.commit()

        print(f"🔥 Berhasil menyimpan {len(preferences)} preferensi dosen! 🔥")
        print("📌 Penggunaan timeslot:")
        for timeslot_id, count in penggunaan_timeslot.items():
            print(f"Timeslot {timeslot_id}: {count} preferensi")
    except Exception as e:
        print(f"🚨 Terjadi kesalahan: {e}")
        session.rollback()
    finally:
        session.close()

# Jalankan generator preferensi
generate_preferences()
