from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal
from model.user_model import User
from model.dosen_model import Dosen

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# List of lecturers (dosen)
lecturers = [
    "Ahmad Hidayatullah",
    "Ahmad Muzaki",
    "Hasan Basri",
    "Rahmi Meldayati",
    "Ainur Alam Budi Utomo",
    "Fajar Setyaning Dwi Putra",
    "Johan Maulana",
    "Abdullah Arif",
    "Ohan Burhanudin",
    "Lilik Zulaihah",
    "Haryanti Jaya Harjani",
    "Ernalem Bangun",
    "Mulyadi",
    "Khozinatun Masfufah",
    "Nurjanah",
    "Sunardin"
]

def hash_password(password: str) -> str:
    """Hash a password for security."""
    return pwd_context.hash(password)

def insert_lecturers_to_user_and_dosen(lecturers):
    """Insert lecturers into the User and Dosen tables."""
    session = SessionLocal()
    pegawai_id_start = 9200  # Starting pegawai_id
    current_pegawai_id = pegawai_id_start
    duplicates = []

    try:
        for fullname in lecturers:
            # Generate email
            email = fullname.strip().replace(" ", "").lower() + "@example.com"

            # Check if the user already exists
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                print(f"Duplicate found: {fullname} ({email})")
                duplicates.append(fullname)
                continue

            # Insert into User table
            new_user = User(
                fullname=fullname,
                email=email,
                password=hash_password("dosen"),  # Default password for all users
                role="dosen"
            )
            session.add(new_user)
            session.commit()  # Commit to get the generated user_id
            user_id = new_user.id

            # Insert into Dosen table
            new_dosen = Dosen(
                pegawai_id=current_pegawai_id,
                nidn=None,  # Set to None or default value
                nip=None,  # Set to None or default value
                nomor_ktp=None,  # Set to None or default value
                nama=fullname,
                tanggal_lahir="2005-05-29 00:00:00",  # Set to None or provide a default value
                progdi_id=1,  # Example progdi_id, adjust based on your use case
                ijin_mengajar=True,  # Default value for ijin_mengajar
                jabatan=None,  # Example jabatan, adjust as needed
                title_depan=None,  # Set to None or default value
                title_belakang=None,  # Set to None or default value
                jabatan_id=0,  # Example jabatan_id, adjust as needed
                is_sekdos=0,  # Default value for is_sekdos
                is_dosen_kb=0,  # Example value for is_dosen_kb
                user_id=user_id  # Link to the User table
            )
            session.add(new_dosen)
            session.commit()  # Commit to save the Dosen entry
            print(f"Inserted: {fullname} with pegawai_id={current_pegawai_id} and user_id={user_id}")

            # Increment pegawai_id for the next entry
            current_pegawai_id += 1

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

# Run the insertion
insert_lecturers_to_user_and_dosen(lecturers)
