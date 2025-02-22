from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, List, Optional


from database import get_db
from pydantic import BaseModel
from model.mahasiswa_model import Mahasiswa
from model.programstudi_model import ProgramStudi
from model.user_model import User  # Import the User model
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password for security."""
    return pwd_context.hash(password)

router = APIRouter()

class UserRead(BaseModel):
    id: int
    nim_nip: str

# Pydantic Models
class MahasiswaBase(BaseModel):
    nama: str
    tahun_masuk: int
    semester: int
    sks_diambil: int
    user_id: int
    program_studi_id: int
    
    tgl_lahir: date
    kota_lahir: str
    jenis_kelamin: str
    kewarganegaraan: str
    alamat: str
    kode_pos: Optional[int] = None
    hp: str



class MahasiswaCreate(BaseModel):
    nim_nip: str  # ✅ Required for creating a user
    password: str  # ✅ Password must be provided
    nama: str
    tahun_masuk: int
    semester: int = 1
    sks_diambil: int = 0
    program_studi_id: int

    tgl_lahir: Optional[date] = None
    kota_lahir: Optional[str] = None
    jenis_kelamin: str = "L"
    kewarganegaraan: Optional[str] = "Indonesia"
    alamat: Optional[str] = None
    kode_pos: Optional[int] = None
    hp: str



class MahasiswaUpdate(BaseModel):
    nim_nip: Optional[str] = None  # ✅ Allow updating NIM
    password: Optional[str] = None  # ✅ Allow updating Password
    nama: Optional[str] = None
    tahun_masuk: Optional[int] = None
    semester: Optional[int] = None
    sks_diambil: Optional[int] = None
    program_studi_id: Optional[int] = None
    tgl_lahir: Optional[date] = None
    kota_lahir: Optional[str] = None
    jenis_kelamin: Optional[str] = None
    kewarganegaraan: Optional[str] = None
    alamat: Optional[str] = None
    kode_pos: Optional[int] = None
    hp: Optional[str] = None

class MahasiswaRead(BaseModel):
    id: int
    nama: str
    tahun_masuk: int
    semester: int
    sks_diambil: int
    program_studi_id: int
    program_studi_name: Optional[str] = None
    nim_nip: str  # ✅ Return User's nim_nip
    role: str  # ✅ Return role
    tgl_lahir: Optional[date] = None
    kota_lahir: Optional[str] = None
    jenis_kelamin: Optional[str] = None
    kewarganegaraan: Optional[str] = None
    alamat: Optional[str] = None
    kode_pos: Optional[int] = None
    hp: Optional[str] = None

    class Config:
        orm_mode = True


# Create Mahasiswa
@router.post("/", response_model=MahasiswaRead, status_code=status.HTTP_201_CREATED)
async def create_mahasiswa(mahasiswa: MahasiswaCreate, db: Session = Depends(get_db)):
    """
    Create a new Mahasiswa record.
    - **If User does not exist**, create a new User.
    - **If Mahasiswa already exists**, return 409 Conflict.
    """

    # ✅ **Check if User already exists by nim_nip**
    existing_user = db.query(User).filter(User.nim_nip == mahasiswa.nim_nip).first()
    
    if existing_user:
        # Check if this User is already linked to a Mahasiswa
        existing_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.user_id == existing_user.id).first()
        if existing_mahasiswa:
            raise HTTPException(status_code=409, detail="Mahasiswa already exists for this User")
    else:
        # ✅ **Create new User**
        hashed_password = hash_password(mahasiswa.password)  # Hash password
        new_user = User(
            nim_nip=mahasiswa.nim_nip,
            password=hashed_password,
            role="mahasiswa",  # ✅ Auto-assign role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    # ✅ **Create new Mahasiswa**
    new_mahasiswa = Mahasiswa(
        nama=mahasiswa.nama,
        tahun_masuk=mahasiswa.tahun_masuk,
        semester=mahasiswa.semester,
        sks_diambil=mahasiswa.sks_diambil,
        program_studi_id=mahasiswa.program_studi_id,
        tgl_lahir=mahasiswa.tgl_lahir,
        kota_lahir=mahasiswa.kota_lahir,
        jenis_kelamin=mahasiswa.jenis_kelamin,
        kewarganegaraan=mahasiswa.kewarganegaraan,
        alamat=mahasiswa.alamat,
        kode_pos=mahasiswa.kode_pos,
        hp=mahasiswa.hp,
        user_id=new_user.id if not existing_user else existing_user.id,  # ✅ Link to user
    )
    
    db.add(new_mahasiswa)
    db.commit()
    db.refresh(new_mahasiswa)

    return {
        "id": new_mahasiswa.id,
        "nama": new_mahasiswa.nama,
        "tahun_masuk": new_mahasiswa.tahun_masuk,
        "semester": new_mahasiswa.semester,
        "sks_diambil": new_mahasiswa.sks_diambil,
        "program_studi_id": new_mahasiswa.program_studi_id,
        "nim_nip": new_user.nim_nip if not existing_user else existing_user.nim_nip,
        "role": new_user.role if not existing_user else existing_user.role,
        "tgl_lahir": new_mahasiswa.tgl_lahir,
        "kota_lahir": new_mahasiswa.kota_lahir,
        "jenis_kelamin": new_mahasiswa.jenis_kelamin,
        "kewarganegaraan": new_mahasiswa.kewarganegaraan,
        "alamat": new_mahasiswa.alamat,
        "kode_pos": new_mahasiswa.kode_pos,
        "hp": new_mahasiswa.hp,
    }



@router.get("/get-all", response_model=List[MahasiswaRead])
def read_all_mahasiswa(
    db: Session = Depends(get_db),
    semester: Optional[int] = Query(None, description="Filter by semester"),
    program_studi_id: Optional[int] = Query(None, description="Filter by program studi"),
    search: Optional[str] = Query(None, description="Search by user fullname or NIM")
):
    query = db.query(Mahasiswa).options(
        joinedload(Mahasiswa.user),  # Explicitly load the user relationship
        joinedload(Mahasiswa.program_studi)  # Explicitly load program_studi relationship
    )
    
    # Apply joins
    query = query.join(Mahasiswa.user)
    query = query.join(Mahasiswa.program_studi)

    if semester is not None and semester != "Semua":
        query = query.filter(Mahasiswa.semester == semester)

    if program_studi_id is not None:
        query = query.filter(Mahasiswa.program_studi_id == program_studi_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Mahasiswa.nama.ilike(search_pattern),
                User.nim_nip.ilike(search_pattern)
            )
        )

    mahasiswa_list = query.all()
    
    # Create a list to store transformed data
    response_data = []
    
    for mhs in mahasiswa_list:
        # Create a dictionary with all required fields
        mhs_data = {
            "id": mhs.id,
            "nama": mhs.nama,
            "tahun_masuk": mhs.tahun_masuk,
            "semester": mhs.semester,
            "sks_diambil": mhs.sks_diambil,
            "program_studi_id": mhs.program_studi_id,
            "program_studi_name": mhs.program_studi.name if mhs.program_studi else None,
            # Get these fields from the user relationship
            "nim_nip": mhs.user.nim_nip,
            "role": mhs.user.role,
            # Optional fields
            "tgl_lahir": mhs.tgl_lahir,
            "kota_lahir": mhs.kota_lahir,
            "jenis_kelamin": mhs.jenis_kelamin,
            "kewarganegaraan": mhs.kewarganegaraan,
            "alamat": mhs.alamat,
            "kode_pos": mhs.kode_pos,
            "hp": mhs.hp
        }
        response_data.append(mhs_data)

    return response_data


@router.get("/get-mahasiswa", response_model=Dict[str, Any])
async def get_mahasiswa(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or NIM")
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
                    Mahasiswa.nama.ilike(f"%{search}%")
                )
            )
        except ValueError:
            query = query.filter(Mahasiswa.nama.ilike(f"%{search}%"))

    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit

    mahasiswa_list = query.offset((page - 1) * limit).limit(limit).all()

    result = [
        {"id": mhs.id, "fullname": mhs.nama, "nim" : mhs.user.nim_nip} for mhs in mahasiswa_list
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
    """
    Fetch Mahasiswa details including User info.
    """
    db_mahasiswa = db.query(Mahasiswa).join(User).filter(Mahasiswa.id == mahasiswa_id).options(
        joinedload(Mahasiswa.user)  # ✅ Load user data
    ).first()

    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    return {
        "id": db_mahasiswa.id,
        "nama": db_mahasiswa.nama,
        "tahun_masuk": db_mahasiswa.tahun_masuk,
        "semester": db_mahasiswa.semester,
        "sks_diambil": db_mahasiswa.sks_diambil,
        "program_studi_id": db_mahasiswa.program_studi_id,
        "nim_nip": db_mahasiswa.user.nim_nip,
        "role": db_mahasiswa.user.role,
        "tgl_lahir": db_mahasiswa.tgl_lahir,
        "kota_lahir": db_mahasiswa.kota_lahir,
        "jenis_kelamin": db_mahasiswa.jenis_kelamin,
        "kewarganegaraan": db_mahasiswa.kewarganegaraan,
        "alamat": db_mahasiswa.alamat,
        "kode_pos": db_mahasiswa.kode_pos,
        "hp": db_mahasiswa.hp,
    }
# Read All Mahasiswa


# Update Mahasiswa
@router.put("/{mahasiswa_id}", response_model=MahasiswaRead)
async def update_mahasiswa(mahasiswa_id: int, mahasiswa: MahasiswaUpdate, db: Session = Depends(get_db)):
    """
    Update Mahasiswa details and sync User model.
    """
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    # Ensure User exists
    user = db.query(User).filter(User.id == db_mahasiswa.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Update `nim_nip` in User Model
    if mahasiswa.nim_nip and mahasiswa.nim_nip != user.nim_nip:
        existing_user = db.query(User).filter(User.nim_nip == mahasiswa.nim_nip).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="NIM already exists")
        user.nim_nip = mahasiswa.nim_nip

    # ✅ Update password if provided
    if mahasiswa.password:
        user.password = hash_password(mahasiswa.password)

    # ✅ Update Mahasiswa fields
    for key, value in mahasiswa.dict(exclude_unset=True).items():
        if key in ["nim_nip", "password"]:  # These are handled separately
            continue
        setattr(db_mahasiswa, key, value)

    db.commit()
    db.refresh(db_mahasiswa)
    db.refresh(user)  # ✅ Ensure User updates are committed

    return {
        "id": db_mahasiswa.id,
        "nama": db_mahasiswa.nama,
        "tahun_masuk": db_mahasiswa.tahun_masuk,
        "semester": db_mahasiswa.semester,
        "sks_diambil": db_mahasiswa.sks_diambil,
        "program_studi_id": db_mahasiswa.program_studi_id,
        "nim_nip": user.nim_nip,
        "role": user.role,
        "tgl_lahir": db_mahasiswa.tgl_lahir,
        "kota_lahir": db_mahasiswa.kota_lahir,
        "jenis_kelamin": db_mahasiswa.jenis_kelamin,
        "kewarganegaraan": db_mahasiswa.kewarganegaraan,
        "alamat": db_mahasiswa.alamat,
        "kode_pos": db_mahasiswa.kode_pos,
        "hp": db_mahasiswa.hp,
    }

# Delete Mahasiswa
@router.delete("/{mahasiswa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    """
    Delete a Mahasiswa and their associated User account.
    """
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    # ✅ Delete associated User
    db_user = db.query(User).filter(User.id == db_mahasiswa.user_id).first()
    if db_user:
        db.delete(db_user)

    # ✅ Delete Mahasiswa
    db.delete(db_mahasiswa)
    db.commit()

    return {"message": "Mahasiswa and associated user deleted successfully"}
