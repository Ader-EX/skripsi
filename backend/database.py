from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

# Set environment: "office" or "home"
environment = "office"  # Default is home

ENV = os.getenv("ENV", environment)
if ENV == "home":
    load_dotenv(".env.personal")
else:
    load_dotenv(".env.office")

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")
sqliteDB = os.getenv("DATABASE_OFFICE_URL")
print(sqliteDB)

if ENV == "home":
    DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    connect_args = {}
else:
    DATABASE_URL = sqliteDB
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Create session and base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from model.dosen_model import Dosen
    from model.listkelas_model import ListKelas
    from model.mahasiswa_model import Mahasiswa
    from model.matakuliah_model import MataKuliah
    from model.pengajaran_model import Pengajaran
    from model.preference_model import Preference
    from model.ruangan_model import Ruangan
    from model.timeslot_model import TimeSlot
    from model.mahasiswatimetable_model import MahasiswaTimeTable
    from model.user_model import User
    from model.timetable_model import TimeTable
    from model.openedclass_model import OpenedClass

    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
