from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from model.ruangan_model import Ruangan
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class RuanganCreate(BaseModel):
    kode_ruangan: str
    nama_ruang: str
    tipe_ruangan: str
    jenis_ruang: str
    kapasitas: int
    alamat: Optional[str] = None
    kode_mapping: Optional[str] = None
    gedung: Optional[str] = None

class RuanganRead(BaseModel):
    id: int
    kode_ruangan: str
    nama_ruang: str
    tipe_ruangan: str
    jenis_ruang: str
    kapasitas: int
    alamat: Optional[str]
    kode_mapping: Optional[str]
    gedung: Optional[str]

    class Config:
        orm_mode = True

@router.post("/ruangan", response_model=RuanganRead, status_code=status.HTTP_201_CREATED)
async def create_ruangan(ruangan: RuanganCreate, db: Session = Depends(get_db)):
    # Check if ruangan already exists
    db_ruangan = db.query(Ruangan).filter(Ruangan.kode_ruangan == ruangan.kode_ruangan).first()
    if db_ruangan:
        raise HTTPException(status_code=400, detail="Ruangan with this kode_ruangan already exists")

    new_ruangan = Ruangan(**ruangan.dict())
    db.add(new_ruangan)
    db.commit()
    db.refresh(new_ruangan)
    return new_ruangan

@router.get("/ruangan/{ruangan_id}", response_model=RuanganRead)
async def get_ruangan(ruangan_id: int, db: Session = Depends(get_db)):
    ruangan = db.query(Ruangan).filter(Ruangan.id == ruangan_id).first()
    if not ruangan:
        raise HTTPException(status_code=404, detail="Ruangan not found")
    return ruangan

@router.get("/ruangan", response_model=List[RuanganRead])
async def get_all_ruangan(
        jenis : Optional[str] = Query(None, description="Tipe Ruangan P | T"),
        db: Session = Depends(get_db)
):
    query = db.query(Ruangan)
    if jenis is not None:
        query = query.filter(Ruangan.jenis_ruang == jenis)
    return query.all()

@router.put("/ruangan/{ruangan_id}", response_model=RuanganRead)
async def update_ruangan(ruangan_id: int, updated_ruangan: RuanganCreate, db: Session = Depends(get_db)):
    ruangan = db.query(Ruangan).filter(Ruangan.id == ruangan_id).first()
    if not ruangan:
        raise HTTPException(status_code=404, detail="Ruangan not found")

    for key, value in updated_ruangan.dict().items():
        setattr(ruangan, key, value)

    db.commit()
    db.refresh(ruangan)
    return ruangan

@router.delete("/ruangan/{ruangan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ruangan(ruangan_id: int, db: Session = Depends(get_db)):
    ruangan = db.query(Ruangan).filter(Ruangan.id == ruangan_id).first()
    if not ruangan:
        raise HTTPException(status_code=404, detail="Ruangan not found")

    db.delete(ruangan)
    db.commit()
    return {"message": "Ruangan deleted successfully"}
