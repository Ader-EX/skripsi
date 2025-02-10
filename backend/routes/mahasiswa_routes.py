from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, List, Optional

from database import get_db
from pydantic import BaseModel, EmailStr
from model.mahasiswa_model import Mahasiswa
from model.programstudi_model import ProgramStudi
from model.user_model import User  # Import the User model

router = APIRouter()

class UserRead(BaseModel):
    id: int
    fullname: str
    email: EmailStr

# Pydantic Models
class MahasiswaBase(BaseModel):
    program_studi_id: int
    tahun_masuk: int
    semester: int
    sks_diambil: int
    user_id: int
   
    tgl_lahir: date
    kota_lahir: str
    jenis_kelamin: str
    kewarganegaraan: str
    alamat: str
    kode_pos: Optional[int] = None
    hp: str

class MahasiswaUpdate(BaseModel):
    program_studi_id: Optional[int] = None
    tahun_masuk: Optional[int] = None
    semester: Optional[int] = None
    sks_diambil: Optional[int] = None
    
    tgl_lahir: Optional[date] = None
    kota_lahir: Optional[str] = None
    jenis_kelamin: Optional[str] = None
    kewarganegaraan: Optional[str] = None
    alamat: Optional[str] = None
    kode_pos: Optional[int] = None
    hp: Optional[str] = None


class MahasiswaCreate(BaseModel):
    user_id: Optional[int] = None  # ✅ Make user_id optional
    program_studi_id: int
    tahun_masuk: int
    semester: int
    sks_diambil: int
    tgl_lahir: Optional[date] = None  # ✅ Allow null dates
    kota_lahir: Optional[str] = None
    jenis_kelamin: str
    kewarganegaraan: Optional[str] = None
    alamat: Optional[str] = None
    kode_pos: Optional[int] = None
    hp: str



class MahasiswaRead(BaseModel):
    id: int
    program_studi_id: int
    program_studi_name : Optional[str] = None
    tahun_masuk: int
    semester: int
    sks_diambil: int
    user: UserRead 
    tgl_lahir: Optional[date] = None
    kota_lahir: Optional[str] = None
    jenis_kelamin: Optional[str] = None
    kewarganegaraan: Optional[str] = None
    alamat: Optional[str] = None
    kode_pos: Optional[int] = None
    hp: Optional[str] = None


    class Config:
        orm_mode = True


    class Config:
        orm_mode = True

# Create Mahasiswa
@router.post("/", response_model=MahasiswaRead, status_code=status.HTTP_201_CREATED)
async def create_mahasiswa(mahasiswa: MahasiswaCreate, db: Session = Depends(get_db)):
    """
    Create a new Mahasiswa record.
    - If the user already exists, link to existing user.
    - If the user does not exist, create a new one.
    - If Mahasiswa already exists for a user, return 409 Conflict.
    """

    # 1️⃣ **Check if user exists by user_id**
    if mahasiswa.user_id:
        user = db.query(User).filter(User.id == mahasiswa.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        raise HTTPException(status_code=400, detail="User ID is required")

    # 2️⃣ **Check if Mahasiswa record already exists**
    existing_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.user_id == mahasiswa.user_id).first()
    if existing_mahasiswa:
        raise HTTPException(status_code=409, detail="Mahasiswa data already exists for this user")

    # 3️⃣ **Create Mahasiswa Record**
    db_mahasiswa = Mahasiswa(**mahasiswa.dict(exclude_unset=True))
    db.add(db_mahasiswa)
    db.commit()
    db.refresh(db_mahasiswa)

    return db_mahasiswa




@router.get("/get-all", response_model=List[MahasiswaRead])
def read_all_mahasiswa(
    db: Session = Depends(get_db),
    semester: Optional[int] = Query(None, description="Filter by semester"),
    program_studi_id: Optional[int] = Query(None, description="Filter by program studi"),
    search: Optional[str] = Query(None, description="Search by user fullname or email")
):
    query = db.query(Mahasiswa).join(User).join(ProgramStudi).options(
        joinedload(Mahasiswa.user),  # Ensure user data is loaded
        joinedload(Mahasiswa.program_studi)  # Ensure program studi data is loaded
    )

    if semester is not None or semester ==  "Semua":
        query = query.filter(Mahasiswa.semester == semester)

    if program_studi_id is not None :
        query = query.filter(Mahasiswa.program_studi_id == program_studi_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.fullname.ilike(search_pattern)) | 
            (User.email.ilike(search_pattern))
        )

    mahasiswa_list = query.all()

    # Add program studi name to each mahasiswa
    for mahasiswa in mahasiswa_list:
        mahasiswa.program_studi_name = mahasiswa.program_studi.name

    return mahasiswa_list

@router.get("/get-mahasiswa", response_model=Dict[str, Any])
async def get_mahasiswa(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or ID")
):
    query = (
        db.query(Mahasiswa)
        .join(User)
        .options(joinedload(Mahasiswa.user))  # ✅ Load user data
    )

    if search:
        try:
            search_id = int(search)
            query = query.filter(
                or_(
                    Mahasiswa.id == search_id,
                    User.fullname.ilike(f"%{search}%")
                )
            )
        except ValueError:
            query = query.filter(User.fullname.ilike(f"%{search}%"))

    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit

    mahasiswa_list = query.offset((page - 1) * limit).limit(limit).all()

    result = [
        {"id": mhs.id, "fullname": mhs.user.fullname} for mhs in mahasiswa_list
    ]

    return dict(
        page=page,
        limit=limit,
        total_pages=total_pages,
        total_records=total_records,
        data=result
    )

# Read Mahasiswa by ID
@router.get("/{mahasiswa_id}", response_model=MahasiswaRead)
async def read_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")
    return db_mahasiswa

# Read All Mahasiswa


# Update Mahasiswa
@router.put("/{mahasiswa_id}", response_model=MahasiswaRead)
async def update_mahasiswa(mahasiswa_id: int, mahasiswa: MahasiswaUpdate, db: Session = Depends(get_db)):
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    # Ensure the User exists
    user = db.query(User).filter(User.id == db_mahasiswa.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with the given user_id not found")

    for key, value in mahasiswa.dict(exclude_unset=True).items():
        setattr(db_mahasiswa, key, value)

    db.commit()
    db.refresh(db_mahasiswa)
    return db_mahasiswa

# Delete Mahasiswa
@router.delete("/{mahasiswa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    db.delete(db_mahasiswa)
    db.commit()
    return {"message": "Mahasiswa deleted successfully"}