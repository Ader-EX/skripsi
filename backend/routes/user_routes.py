from typing import List, Optional, Union
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
from enum import Enum  

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 300))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

class RoleEnum(str, Enum):
    mahasiswa = "mahasiswa"
    dosen = "dosen"
    admin = "admin"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
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
    nim_nip: str
    password: str
    role: RoleEnum 

class UserRead(BaseModel):
    id: int
    nim_nip: str
    role: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    role_id: Optional[int] = None
    prodi_id : Optional[int] = None


class TokenData(BaseModel):
    nim_nip: Optional[str] = None

class MahasiswaDetails(BaseModel):
    id: int
    role: str
    nama: str
    tahun_masuk: int
    semester: int
    sks_diambil: int
    tgl_lahir: str
    kota_lahir: str
    jenis_kelamin: str
    kewarganegaraan: str
    alamat: str
    kode_pos: Optional[int]
    hp: str
    program_studi_id: int

class DosenDetails(BaseModel):
    pegawai_id: int
    role: str
    nidn: Optional[str]
    nomor_ktp: Optional[str]
    email: Optional[str]
    tanggal_lahir: Optional[str]
    progdi_id: Optional[int]
    ijin_mengajar: bool
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    jabatan_id: Optional[int]
    is_sekdos: bool
    

class LoginRequest(BaseModel):
    nim_nip: str
    password: str

@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.nim_nip == user.nim_nip).first()
    if db_user:
        raise HTTPException(status_code=400, detail="NIM/NIP sudah terdaftar")

    hashed_password = hash_password(user.password)

    new_user = User(
        nim_nip=user.nim_nip,
        password=hashed_password,
        role=user.role.value,  
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

  
    if user.role == RoleEnum.mahasiswa:
        new_mahasiswa = Mahasiswa(
            user_id=new_user.id,
            nama="",
            tahun_masuk=0,
            semester=0,
            sks_diambil=0,
            tgl_lahir=None,
            kota_lahir="",
            jenis_kelamin="",
            kewarganegaraan="",
            alamat="",
            kode_pos=None,
            hp="",
            program_studi_id=1
        )
        db.add(new_mahasiswa)

    elif user.role == RoleEnum.dosen:
        new_dosen = Dosen(
            user_id=new_user.id,
            nidn=None,
            nomor_ktp=None,
            email=None,
            tanggal_lahir=None,
            progdi_id=None,
            ijin_mengajar=True,
            jabatan=None,
            title_depan=None,
            title_belakang=None,
            
        )
        db.add(new_dosen)

    db.commit()
    return new_user

@router.get("/details")
async def get_user_details(
    nim_nip: str = Query(..., description="NIM/NIP dari user yang ingin diambil detailnya"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.nim_nip == nim_nip).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if user.role == "mahasiswa":
        mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.user_id == user.id).first()
        if not mahasiswa:
            raise HTTPException(status_code=404, detail="Mahasiswa details tidak ditemukan")

        return MahasiswaDetails(
            id=mahasiswa.id,
            role=user.role,
            nama=mahasiswa.nama,
            tahun_masuk=mahasiswa.tahun_masuk,
            semester=mahasiswa.semester,
            sks_diambil=mahasiswa.sks_diambil,
            tgl_lahir=mahasiswa.tgl_lahir.strftime("%Y-%m-%d") if mahasiswa.tgl_lahir else None,
            kota_lahir=mahasiswa.kota_lahir,
            jenis_kelamin=mahasiswa.jenis_kelamin,
            kewarganegaraan=mahasiswa.kewarganegaraan,
            alamat=mahasiswa.alamat,
            kode_pos=mahasiswa.kode_pos,
            hp=mahasiswa.hp,
            program_studi_id=mahasiswa.program_studi_id
        )

    elif user.role == "dosen":
        dosen = db.query(Dosen).filter(Dosen.user_id == user.id).first()
        if not dosen:
            raise HTTPException(status_code=404, detail="Dosen details  tidak ditemukan")

        return DosenDetails(
            pegawai_id=dosen.pegawai_id,
            role=user.role,
            nidn=dosen.nidn,
            nomor_ktp=dosen.nomor_ktp,
            email=dosen.email,
            tanggal_lahir=dosen.tanggal_lahir.strftime("%Y-%m-%d") if dosen.tanggal_lahir else None,
            progdi_id=dosen.progdi_id,
            ijin_mengajar=dosen.ijin_mengajar,
            jabatan=dosen.jabatan,
            title_depan=dosen.title_depan,
            title_belakang=dosen.title_belakang,
            jabatan_id=dosen.jabatan_id,
            is_sekdos=dosen.is_sekdos,
            
        )

    raise HTTPException(status_code=400, detail="Invalid user role")

@router.get("/users", response_model=List[UserRead])
async def get_all_users(role: Optional[RoleEnum] = Query(None, description="Filter users dengan role"),
                        db: Session = Depends(get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.value)
    users = query.all()
    return users

@router.post("/token", response_model=Token)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.nim_nip == login_request.nim_nip).first()
    
    if not user or not verify_password(login_request.password, user.password):
        raise HTTPException(status_code=401, detail="NIM/NIP or password salah")

    role_id = None
    user_name = user.nim_nip
    prodi_id = None

    if user.role == "mahasiswa":
        mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.user_id == user.id).first()
        role_id = mahasiswa.id if mahasiswa else None
        user_name = mahasiswa.nama if mahasiswa else user.nim_nip
        prodi_id = mahasiswa.program_studi_id if mahasiswa else None
    elif user.role == "dosen":
        dosen = db.query(Dosen).filter(Dosen.user_id == user.id).first()
        role_id = dosen.pegawai_id if dosen else None
        user_name = dosen.nama if dosen else user.nim_nip
        prodi_id = dosen.progdi_id if dosen else None
    elif user.role == "admin":
        role_id = None
        prodi_id = None
    else:
        raise HTTPException(status_code=400, detail="Invalid user role")

    
    token_data = {
        "sub": user.nim_nip,
        "role": user.role,
        "user_id": user.id,
        "name": user_name  
    }

    if role_id is not None:
        token_data["role_id"] = role_id
    
    if prodi_id is not None:
        token_data["prodi_id"] = prodi_id

    access_token = create_access_token(data=token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "role_id": role_id,
    }



@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    if user.role == "mahasiswa":
        mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.user_id == user.id).first()
        if mahasiswa:
            db.delete(mahasiswa)
    elif user.role == "dosen":
        dosen = db.query(Dosen).filter(Dosen.user_id == user.id).first()
        if dosen:
            db.delete(dosen)
    
    db.delete(user)
    db.commit()
    return {"message": "User berhasil dihapus"}

@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, updated_user: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    user.nim_nip = updated_user.nim_nip
    user.password = hash_password(updated_user.password)
    user.role = updated_user.role.value
    db.commit()
    db.refresh(user)
    return user