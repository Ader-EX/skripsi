import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
from model.temporary_timetable_model import TemporaryTimeTable
from datetime import datetime

# Import all routes
from routes.user_routes import router as user_router
from routes.dosen_routes import router as dosen_router
from routes.matakuliah_routes import router as matakuliah_router
from routes.ruangan_routes import router as ruangan_router
from routes.mahasiswa_routes import router as mahasiswa_router
from routes.timeslot_routes import router as timeslot_router
from routes.preference_routes import router as preference_router
from routes.programstudi_routes import router as programstudi_router
from routes.openedclass_routes import router as openedclass_router
from routes.academicperiod_routes import router as academicperiod_router
from routes.mahasiswatimetable_routes import router as mahasiswatimetable_router
from routes.algorithm_routes import router as algorithm_router
from routes.timetable_routes import router as timetable_router
from routes.admin_routes import router as admin_router
from routes.dosenopened_routes import router as dosenopened_router
from routes.sa_routes import router as sa_router
from routes.ga_routes import router as ga_router
from routes.hybrid_routes import router as hybrid_router
from routes.temporary_timetable_routes import router as temporary_timetable_router
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


bearer_scheme = HTTPBearer(auto_error=False)

def verify_token_except_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
  
    if request.url.path.startswith("/user"):
        return

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing token"
        )
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing token"
        )
    return payload  


scheduler = BackgroundScheduler()

def cleanup_expired_temporary_timetables():
    db: Session = SessionLocal()
    try:
        now = datetime.now()
        expired_entries = db.query(TemporaryTimeTable).filter(TemporaryTimeTable.end_date < now).all()

        if expired_entries:
            print(f"[{datetime.now()}] Deleting {len(expired_entries)} expired temporary timetables...")

        for entry in expired_entries:
            db.delete(entry)

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"[{datetime.now()}] Cleanup failed:", str(e))
    finally:
        db.close()

scheduler.add_job(cleanup_expired_temporary_timetables, 'interval', minutes=20)


app = FastAPI(
    dependencies=[Depends(verify_token_except_user)],
    swagger_ui_parameters={"syntaxHighlight.theme": "monokai"}
)



# origins = ["http://localhost:3000"]
origins = [
    "http://localhost:3000",
    "https://skripsi-penjadwalan-upn.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    from database import create_tables
    # create_tables()

    # Start APScheduler di startup
    scheduler.start()
    print("Scheduler started ✅")

@app.get("/public", dependencies=[])
async def public_endpoint():
    return {"message": "This endpoint is public"}

@app.get("/")
async def test_hello():
    return {"message": "Test"}


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shutdown ✅")



app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(dosen_router, prefix="/dosen", tags=["Dosen"])
app.include_router(matakuliah_router, prefix="/matakuliah", tags=["MataKuliah"])
app.include_router(ruangan_router, prefix="/ruangan", tags=["Ruangan"])
app.include_router(mahasiswa_router, prefix="/mahasiswa", tags=["Mahasiswa"])
app.include_router(timeslot_router, prefix="/timeslot", tags=["TimeSlot"])
app.include_router(preference_router, prefix="/preference", tags=["Preference"])
app.include_router(programstudi_router, prefix="/program-studi", tags=["Program Studi"])
app.include_router(openedclass_router, prefix="/opened-class", tags=["Opened Class"])
app.include_router(academicperiod_router, prefix="/academic-period", tags=["Academic Period"])
app.include_router(mahasiswatimetable_router, prefix="/mahasiswa-timetable", tags=["Mahasiswa Timetable"])
app.include_router(algorithm_router, prefix="/algorithm", tags=["Genetic Algorithm"])
app.include_router(timetable_router, prefix="/timetable", tags=["Timetable"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(dosenopened_router, prefix="/dosen-opened", tags=["Dosen Opened Class"])
app.include_router(sa_router, prefix="/sa-router", tags=["Simulated Annealing"])
app.include_router(ga_router, prefix="/ga-router", tags=["Genetic Algorithm"])
app.include_router(hybrid_router, prefix="/hybrid-router", tags=["Hybrid Algorithm"])
app.include_router(temporary_timetable_router, prefix="/temporary-timetable", tags=["Temporary Timetable"])
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
