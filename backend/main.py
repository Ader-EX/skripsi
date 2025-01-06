from typing import List
from fastapi import Depends, FastAPI, HTTPException, status, Response
from database import Base, SessionLocal, engine, create_tables
from fastapi.middleware.cors import CORSMiddleware

# Import all model
from model.dosen_model import Dosen
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

# Import all routes
from routes.user_routes import router as user_router
from routes.dosen_routes import router as dosen_router
from routes.matakuliah_routes import router as matakuliah_router

# Initialize the FastAPI application
app = FastAPI(
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai"
    }
)



# Replace the default Swagger UI with the custom one
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return custom_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Docs"
    )


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.on_event("startup")
async def startup_event():
    create_tables()


# Test endpoint
@app.get("/")
async def test_hello():
    return {
        "message": "Test"
    }


app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(dosen_router,prefix="/dosen", tags=["Dosen"])
app.include_router(matakuliah_router, prefix="/matakuliah", tags=["MataKuliah"])