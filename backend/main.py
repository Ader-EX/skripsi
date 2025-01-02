from typing import List
from fastapi import Depends, FastAPI, HTTPException, status
from database import Base, SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware

from model.dosen_model import Dosen  # Import all model
from model.admin_model import Admin
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

# Initialize the FastAPI application
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow specific origin
    allow_credentials=True,  # If you need to support credentials (e.g., cookies)
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Function to initialize database tables
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

# Call `create_tables()` when the app starts
@app.on_event("startup")
async def startup_event():
    create_tables()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test endpoint
@app.get("/")
async def test_hello():
    return {
        "message": "Test"
    }
