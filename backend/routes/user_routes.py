from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from model.dosen_model import Dosen
from model.mahasiswa_model import Mahasiswa
from database import get_db
from model.user_model import User
from pydantic import BaseModel
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from jwt import encode, decode
from datetime import datetime, timedelta, timezone
from enum import Enum  # Import Enum for predefined options

# Load environment variables from .env file
load_dotenv()

# Get configurations from .env
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


# Enum for Role Options
class RoleEnum(str, Enum):
    mahasiswa = "mahasiswa"
    dosen = "dosen"
    admin = "admin"


# Utility functions for password hashing and JWT
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Pydantic models
class UserCreate(BaseModel):
    fullname: str
    email: str
    password: str
    role: RoleEnum  # Use Enum for predefined options


class UserRead(BaseModel):
    id: int
    fullname: str
    email: str
    role: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Routes
@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)

    # Create user
    new_user = User(
        fullname=user.fullname,
        email=user.email,
        password=hashed_password,
        role=user.role.value,  # Get the string value of the Enum
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # ✅ Populate the correct role table
    if user.role == RoleEnum.mahasiswa:
        new_mahasiswa = Mahasiswa(
            user_id=new_user.id,
            tahun_masuk=2024,  
            semester=1,
            sks_diambil=0,
            nama=new_user.fullname,
            tgl_lahir="2000-01-01",
            kota_lahir="Unknown",
            jenis_kelamin="Unknown",
            kewarganegaraan="Unknown",
            alamat="Unknown",
            kode_pos=None,
            hp="Unknown",
            email=new_user.email,
            nama_ayah=None,
            nama_ibu=None,
            pekerjaan_ayah=None,
            pekerjaan_ibu=None,
            status_kawin=False,
            program_studi_id=1  
        )
        db.add(new_mahasiswa)

    elif user.role == RoleEnum.dosen:
        new_dosen = Dosen(
            user_id=new_user.id,
            pegawai_id=None,
            nidn=None,
            nip=None,
            nomor_ktp=None,
            nama=new_user.fullname,
            tanggal_lahir=None,
            progdi_id=None,
            ijin_mengajar=True,
            jabatan=None,
            title_depan=None,
            title_belakang=None,
            jabatan_id=None,
            is_sekdos=False,
            is_dosen_kb=False
        )
        db.add(new_dosen)

    # No extra table for Admin, just use User table

    db.commit()
    return new_user

class UserDetails(BaseModel):
    id: str
    role: str

class MahasiswaDetails(BaseModel):
    id: int
    role: str
    fullname: str
    email: str
    tahun_masuk: int
    semester: int
    sks_diambil: int
    nama: str
    tgl_lahir: str
    kota_lahir: str
    jenis_kelamin: str
    kewarganegaraan: str
    alamat: str
    kode_pos: Optional[int]
    hp: str
    nama_ayah: Optional[str]
    nama_ibu: Optional[str]
    pekerjaan_ayah: Optional[str]
    pekerjaan_ibu: Optional[str]
    status_kawin: bool
    program_studi_id: int

class DosenDetails(BaseModel):
    id: int
    role: str
    fullname: str
    email: str
    nidn: Optional[str]
    nip: Optional[str]
    nomor_ktp: Optional[str]
    nama: Optional[str]
    tanggal_lahir: Optional[str]
    progdi_id: Optional[int]
    ijin_mengajar: bool
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    is_sekdos: bool
    is_dosen_kb: bool

class AdminDetails(BaseModel):
    id: int
    role: str
    fullname: str
    email: str

@router.get("/details")
async def get_user_details(
    email: str = Query(..., description="The email of the user"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # If user is a Mahasiswa
    if user.role == "mahasiswa":
        mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.user_id == user.id).first()
        if not mahasiswa:
            raise HTTPException(status_code=404, detail="Mahasiswa details not found")

        return MahasiswaDetails(
            id=mahasiswa.id,
            role=user.role,
            fullname=user.fullname,
            email=user.email,
            tahun_masuk=mahasiswa.tahun_masuk,
            semester=mahasiswa.semester,
            sks_diambil=mahasiswa.sks_diambil,
            nama=mahasiswa.nama,
            tgl_lahir=mahasiswa.tgl_lahir.strftime("%Y-%m-%d"),
            kota_lahir=mahasiswa.kota_lahir,
            jenis_kelamin=mahasiswa.jenis_kelamin,
            kewarganegaraan=mahasiswa.kewarganegaraan,
            alamat=mahasiswa.alamat,
            kode_pos=mahasiswa.kode_pos,
            hp=mahasiswa.hp,
            nama_ayah=mahasiswa.nama_ayah,
            nama_ibu=mahasiswa.nama_ibu,
            pekerjaan_ayah=mahasiswa.pekerjaan_ayah,
            pekerjaan_ibu=mahasiswa.pekerjaan_ibu,
            status_kawin=mahasiswa.status_kawin,
            program_studi_id=mahasiswa.program_studi_id
        )

    # If user is a Dosen
    elif user.role == "dosen":
        dosen = db.query(Dosen).filter(Dosen.user_id == user.id).first()
        if not dosen:
            raise HTTPException(status_code=404, detail="Dosen details not found")

        return DosenDetails(
            id=dosen.id,
            role=user.role,
            fullname=user.fullname,
            email=user.email,
            nidn=dosen.nidn,
            nip=dosen.nip,
            nomor_ktp=dosen.nomor_ktp,
            nama=dosen.nama,
            tanggal_lahir=dosen.tanggal_lahir.strftime("%Y-%m-%d") if dosen.tanggal_lahir else None,
            progdi_id=dosen.progdi_id,
            ijin_mengajar=dosen.ijin_mengajar,
            jabatan=dosen.jabatan,
            title_depan=dosen.title_depan,
            title_belakang=dosen.title_belakang,
            is_sekdos=dosen.is_sekdos,
            is_dosen_kb=dosen.is_dosen_kb,
        )

    # If user is an Admin, return only basic details
    elif user.role == "admin":
        return AdminDetails(
            id=user.id,
            role=user.role,
            fullname=user.fullname,
            email=user.email,
        )

    # If role is unknown, return error
    raise HTTPException(status_code=400, detail="Invalid user role")

@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users", response_model=List[UserRead])
async def get_all_users(role: Optional[RoleEnum] = Query(None, description="Filter users by role"),
                        db: Session = Depends(get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.value)
    users = query.all()
    return users

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, updated_user: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.fullname = updated_user.fullname
    user.email = updated_user.email
    user.password = hash_password(updated_user.password)
    user.role = updated_user.role.value
    db.commit()
    db.refresh(user)
    return user


class LoginRequest(BaseModel):
    email: str
    password: str



@router.post("/token", response_model=Token)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_request.email).first()
    if not user or not verify_password(login_request.password, user.password):
        raise HTTPException(status_code=401, detail="Username or password is incorrect")
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


