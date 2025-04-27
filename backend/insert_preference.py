import random
from sqlalchemy.orm import Session
from model import Dosen, TimeSlot, Preference
from database import SessionLocal


def generate_random_preferences():
    db: Session = SessionLocal()
    try:
        dosen_list = db.query(Dosen).all()
        timeslot_list = db.query(TimeSlot).all()

        if not dosen_list or not timeslot_list:
            print("Tidak ada dosen atau timeslot tersedia.")
            return

        total_dosen = len(dosen_list)
        special_needs_count = int(total_dosen * 0.15)
        special_needs_dosen_ids = set(random.sample([d.pegawai_id for d in dosen_list], special_needs_count))

        preferences_to_add = []

        for dosen in dosen_list:
            num_preferences = random.randint(0, 4)
            selected_timeslots = random.sample(timeslot_list, k=min(num_preferences, len(timeslot_list)))

            is_special_needs = dosen.pegawai_id in special_needs_dosen_ids

            for ts in selected_timeslots:
                pref = Preference(
                    dosen_id=dosen.pegawai_id,
                    timeslot_id=ts.id,
                    is_special_needs=is_special_needs,
                    is_high_priority=random.choice([True, False]),
                    reason="Generated randomly"
                )
                preferences_to_add.append(pref)

        # Insert semua sekaligus
        db.bulk_save_objects(preferences_to_add)
        db.commit()
        print(f"Berhasil insert {len(preferences_to_add)} preferences ke database.")

    except Exception as e:
        db.rollback()
        print(f"Gagal insert preferences: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    generate_random_preferences()
