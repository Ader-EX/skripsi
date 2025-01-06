from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from database import get_db
from model.matakuliah_model import MataKuliah
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, validator, field_validator

class MataKuliahBase(BaseModel):
    kodemk: str
    namamk: str
    sks: int
    smt: int
    kurikulum: str
    status_mk: str
    kelas: str
    tipe_mk: int

class MataKuliahCreate(MataKuliahBase):
    pass

class MataKuliahRead(MataKuliahBase):
    class Config:
        orm_mode = True

router = APIRouter()

@router.get("/matakuliah", response_model=List[MataKuliahRead], status_code=status.HTTP_200_OK)
async def get_all_matakuliah(program_studi : Optional[str]
                             = Query(None,
                                description= "Cari mata kuliah berdasarkan program studi ")
                             ,db: Session = Depends(get_db)):
    query = db.query(MataKuliah)
    if program_studi:
        query =query.filter(MataKuliah.program_studi == program_studi)
    matakuliahs = query.all()
    return matakuliahs


@router.post("/matakuliah", response_model=MataKuliahRead, status_code=status.HTTP_201_CREATED)
async def create_matakuliah(
        matakuliah: MataKuliahCreate, db: Session = Depends(get_db)
):

    db_matakuliah = MataKuliah(**matakuliah.dict())
    db.add(db_matakuliah)
    db.commit()
    db.refresh(db_matakuliah)
    return db_matakuliah