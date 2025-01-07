import csv
from datetime import datetime
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal
from model.dosen_model import Dosen
from model.user_model import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Path to the CSV file
csv_file_path = "datas/Dosen.csv"

def hash_password(password: str) -> str:
    """Hash a password for security."""
    return pwd_context.hash(password)

def parse_date(date_string):
    """Parses the date in the format 'd/m/Y' to a datetime object."""
    try:
        return datetime.strptime(date_string, "%d/%m/%Y")
    except ValueError:
        return None

def load_csv_to_database(file_path):
    duplicates = []

    # Use SessionLocal from database.py
    session = SessionLocal()

    try:
        with open(file_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                pegawai_id = int(row["f_pegawai_id"])

                # Check if a record with the same pegawai_id already exists in Dosen
                existing_dosen = session.query(Dosen).filter_by(pegawai_id=pegawai_id).first()

                if existing_dosen:
                    duplicates.append(row)
                    continue

                # Check if the user already exists
                existing_user = session.query(User).filter_by(fullname=row["f_namapegawai"]).first()
                if existing_user:
                    duplicates.append(row)
                    continue

                # Create a new user entry
                new_user = User(
                    fullname=row["f_namapegawai"],
                    email=row["f_namapegawai"].strip().replace(" ", "").lower() + "@example.com",
                    password=hash_password("dosen"),  # Default password for all users
                    role="dosen"
                )
                session.add(new_user)
                session.commit()  # Commit to get the generated user_id

                # Create a new dosen entry
                new_dosen = Dosen(
                    pegawai_id=pegawai_id,
                    nidn=row["f_nidn"],
                    nip=row["f_nip"],
                    nomor_ktp=row["f_nomorktp"],
                    nama=row["f_namapegawai"],  # Optionally, remove this column in the Dosen table
                    tanggal_lahir=parse_date(row["f_tanggallahir"]),
                    progdi_id=int(row["f_progdi_id"]),
                    ijin_mengajar=row["f_ijinmengajar"].strip().upper() == "T",
                    jabatan=row["jabatan"],
                    title_depan=row["f_title_depan"],
                    title_belakang=row["f_title_belakang"],
                    jabatan_id=int(row["f_jabatan_id"]),
                    is_sekdos=row["f_sekdos"].strip().upper() == "T",
                    user_id=new_user.id  # Link the user_id from the User table
                )
                session.add(new_dosen)

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
