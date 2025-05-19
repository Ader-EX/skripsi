import random
from sqlalchemy.orm import Session
from sqlalchemy import tuple_
from model import Dosen, TimeSlot, Preference
from database import SessionLocal

def generate_targeted_preferences(total_prefs: int = 200):
    db: Session = SessionLocal()
    try:
        # Definisikan slot‐slot target
        WEEK_DAYS = ["Senin", "Selasa", "Rabu", "Kamis"]
        WEEK_SLOTS = ["07:10:00", "09:40:00", "13:00:00", "15:40:00"]
        FRI_DAY   = "Jumat"
        FRI_SLOTS = ["08:00:00", "09:40:00", "13:30:00", "15:10:00"]

        # bangun list tuple 
        TARGET = [(day, t) for day in WEEK_DAYS for t in WEEK_SLOTS]
        TARGET += [(FRI_DAY, t) for t in FRI_SLOTS]

        #  Ambil semua dosen dan hanya timeslot yg di TARGET
        dosen_list    = db.query(Dosen).all()
        timeslot_list = (
            db.query(TimeSlot)
              .filter(tuple_(TimeSlot.day, TimeSlot.start_time).in_(TARGET))
              .all()
        )

        if not dosen_list or not timeslot_list:
            print("Tidak ada dosen atau timeslot target.")
            return

        # buat kandidat dosen n waktu (dosen_id, timeslot_id)
        candidates = [
            (d.pegawai_id, ts.id)
            for d in dosen_list
            for ts in timeslot_list
        ]

        # shuffle dan ambil teratas
        random.shuffle(candidates)
        selected = candidates[:min(total_prefs, len(candidates))]

        #  Pilih 10% dosen untuk special_needs
        special_count = int(len(dosen_list) * 0.10)
        special_ids   = set(random.sample(
            [d.pegawai_id for d in dosen_list],
            special_count
        ))

        #  untuk high priority
        reasonOptions = [
            "Jadwal bentrok",
            "Tanggung jawab lain",
            "Kesehatan",
            "Jadwal luar kampus",
            "Bimbingan skripsi",
            "Beban kerja tinggi",
            "Hanya bisa di slot ini",
        ]

        to_insert = []
        for dosen_id, ts_id in selected:
            is_special = dosen_id in special_ids
            is_high    = (random.random() < 0.2)
            reason     = random.choice(reasonOptions) if is_high else "General Preference"

            pref = Preference(
                dosen_id         = dosen_id,
                timeslot_id      = ts_id,
                is_special_needs = is_special,
                is_high_priority = is_high,
                reason           = reason
            )
            to_insert.append(pref)

        db.bulk_save_objects(to_insert)
        db.commit()
        print(f"Berhasil insert {len(to_insert)} preferences (max {total_prefs}).")

    except Exception as e:
        db.rollback()
        print("Gagal:", e)
    finally:
        db.close()


if __name__ == "__main__":
    generate_targeted_preferences()
