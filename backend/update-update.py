import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from model.dosen_model import Dosen
from datetime import datetime

# Path to the CSV fil
csv_file_path = "datas/hasil/dosen.csv"

def safe_value(value):
    """ Converts NaN values to None for MySQL compatibility. """
    return None if pd.isna(value) else value

def safe_bool(value):
    """ Converts possible boolean/int values into actual boolean. """
    return bool(int(value)) if pd.notna(value) else None

def safe_date(value):
    """ Converts possible date strings into Python datetime.date. """
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date() if pd.notna(value) else None
    except ValueError:
        return None  # If format is incorrect, return None

def load_csv_to_database(file_path):
    session = SessionLocal()

    try:
        # Read the CSV file
        df = pd.read_csv(file_path)

        for _, row in df.iterrows():
            # Convert NaN values to None
            dosen = Dosen(
                id=safe_value(row['id']),
                pegawai_id=safe_value(row['pegawai_id']),
                nidn=safe_value(row['nidn']),
                nip=safe_value(row['nip']),
                nomor_ktp=safe_value(row['nomor_ktp']),
                nama=safe_value(row['nama']),
                tanggal_lahir=safe_date(row['tanggal_lahir']),  # ✅ Convert Dates Properly
                progdi_id=safe_value(row['progdi_id']),
                ijin_mengajar=safe_bool(row['ijin_mengajar']),  # ✅ Fix Boolean
                jabatan=safe_value(row['jabatan']),
                title_depan=safe_value(row['title_depan']),
                title_belakang=safe_value(row['title_belakang']),
                jabatan_id=safe_value(row['jabatan_id']),
                is_sekdos=safe_bool(row['is_sekdos']),  # ✅ Fix Boolean
                is_dosen_kb=safe_bool(row['is_dosen_kb']),  # ✅ Fix Boolean
                user_id=safe_value(row['user_id'])
            )
            session.add(dosen)

        # Commit changes
        session.commit()
        print("Dosen data successfully inserted!")

    except Exception as e:
        print("Error occurred:", e)
        session.rollback()
    finally:
        session.close()

# Run the loader
load_csv_to_database(csv_file_path)
