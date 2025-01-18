from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from pydantic import BaseModel
from model.matakuliah_model import MataKuliah
from model.matakuliah_programstudi import MataKuliahProgramStudi

router = APIRouter()

# Pydantic Models
class MataKuliahProgramStudiCreate(BaseModel):
    program_studi_id: int


class MataKuliahBase(BaseModel):
    kodemk: str
    namamk: str
    sks: int
    smt: int
    kurikulum: str
    status_mk: str
    have_kelas_besar: bool
    tipe_mk: int
    program_studi_ids: List[int]  # List of program_studi IDs to associate

    class Config:
        orm_mode = True


class MataKuliahCreate(MataKuliahBase):
    pass


class MataKuliahRead(MataKuliahBase):
    id: str


# CRUD Routes
@router.post("/", response_model=MataKuliahRead, status_code=status.HTTP_201_CREATED)
async def create_matakuliah(matakuliah: MataKuliahCreate, db: Session = Depends(get_db)):
    # Check if the MataKuliah already exists
    existing_matakuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == matakuliah.kodemk).first()
    if existing_matakuliah:
        raise HTTPException(status_code=400, detail="MataKuliah with this kode already exists.")

    # Create MataKuliah
    new_matakuliah = MataKuliah(
        kodemk=matakuliah.kodemk,
        namamk=matakuliah.namamk,
        sks=matakuliah.sks,
        smt=matakuliah.smt,
        kurikulum=matakuliah.kurikulum,
        status_mk=matakuliah.status_mk,
        have_kelas_besar=matakuliah.have_kelas_besar,
        tipe_mk=matakuliah.tipe_mk
    )
    db.add(new_matakuliah)
    db.commit()
    db.refresh(new_matakuliah)

    # Create associations with program_studi in MataKuliahProgramStudi
    for program_studi_id in matakuliah.program_studi_ids:
        association = MataKuliahProgramStudi(
            mata_kuliah_id=new_matakuliah.kodemk,
            program_studi_id=program_studi_id
        )
        db.add(association)

    db.commit()
    return new_matakuliah


@router.get("/", response_model=List[MataKuliahRead])
async def get_all_matakuliah(db: Session = Depends(get_db)):
    return db.query(MataKuliah).all()


@router.get("/{matakuliah_id}", response_model=MataKuliahRead)
async def get_matakuliah(matakuliah_id: str, db: Session = Depends(get_db)):
    matakuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == matakuliah_id).first()
    if not matakuliah:
        raise HTTPException(status_code=404, detail="MataKuliah not found")
    return matakuliah


@router.put("/{matakuliah_id}", response_model=MataKuliahRead)
async def update_matakuliah(matakuliah_id: str, updated_data: MataKuliahCreate, db: Session = Depends(get_db)):
    matakuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == matakuliah_id).first()
    if not matakuliah:
        raise HTTPException(status_code=404, detail="MataKuliah not found")

    # Update MataKuliah fields
    for key, value in updated_data.dict(exclude={"program_studi_ids"}).items():
        setattr(matakuliah, key, value)

    # Update MataKuliahProgramStudi associations
    db.query(MataKuliahProgramStudi).filter(MataKuliahProgramStudi.mata_kuliah_id == matakuliah.kodemk).delete()
    for program_studi_id in updated_data.program_studi_ids:
        association = MataKuliahProgramStudi(
            mata_kuliah_id=matakuliah.kodemk,
            program_studi_id=program_studi_id
        )
        db.add(association)

    db.commit()
    db.refresh(matakuliah)
    return matakuliah


@router.delete("/{matakuliah_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matakuliah(matakuliah_id: str, db: Session = Depends(get_db)):
    matakuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == matakuliah_id).first()
    if not matakuliah:
        raise HTTPException(status_code=404, detail="MataKuliah not found")

    # Delete associations in MataKuliahProgramStudi
    db.query(MataKuliahProgramStudi).filter(MataKuliahProgramStudi.mata_kuliah_id == matakuliah.kodemk).delete()

    # Delete MataKuliah
    db.delete(matakuliah)
    db.commit()
    return {"message": "MataKuliah deleted successfully"}
