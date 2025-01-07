import csv
from sqlalchemy.orm import Session
from database import SessionLocal
from model.ruangan_model import Ruangan

# Path to the CSV file
csv_file_path = "datas/Ruangan.csv"

def extract_group_code(kode_ruangan: str) -> str:
    """
    Extracts the group code based on the floor number from the room code.
    If no floor number is found, assigns 'Other' as the group code.
    """
    try:
        # Extract the floor number from the room code
        floor = int(kode_ruangan.split("-")[1][0])
        if floor == 2:
            return "2nd Floor"
        elif floor == 3:
            return "3rd Floor"
        elif floor == 4:
            return "4th Floor"
        else:
            return "Other"
    except (IndexError, ValueError):
        return "Other"

def load_csv_to_database(file_path):
    duplicates = []

    # Use SessionLocal from database.py
    session = SessionLocal()

    try:
        with open(file_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                ruang_id = int(row["f_ruang_id"])

                # Check if a record with the same ruang_id already exists
                existing_ruangan = session.query(Ruangan).filter_by(id=ruang_id).first()

                if existing_ruangan:
                    duplicates.append(row)
                    continue

                # Extract group code from room code
                group_code = extract_group_code(row["f_koderuang"])

                # Create a new ruangan entry
                new_ruangan = Ruangan(
                    id=ruang_id,
                    kode_ruangan=row["f_koderuang"],
                    nama_ruang=row["f_namaruang"],
                    tipe_ruangan=row["f_tiperuangan"],
                    jenis_ruang=row["f_jenisruang_id"],
                    kapasitas=int(row["f_kapasitas_kuliah"]),
                    group_code=group_code,
                    alamat=row["f_alamatruang"],
                    gedung=row["gedung"]
                )
                session.add(new_ruangan)

        # Commit the session to save changes to the database
        session.commit()

        # Log duplicates
        if duplicates:
            print("Duplicate records found:")
            for dup in duplicates:
                print(dup)

    except Exception as e:
        print("Error occurred:", e)
        session.rollback()
    finally:
        session.close()

# Run the loader
load_csv_to_database(csv_file_path)
