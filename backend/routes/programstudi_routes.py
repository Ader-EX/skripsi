from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from model.programstudi_model import ProgramStudi
from pydantic import BaseModel

router = APIRouter()

# Pydantic Models
class ProgramStudiBase(BaseModel):
    name: str


class ProgramStudiCreate(ProgramStudiBase):
    pass


class ProgramStudiRead(ProgramStudiBase):
    id: int

    class Config:
        orm_mode = True


@router.post("/", response_model=ProgramStudiRead, status_code=status.HTTP_201_CREATED)
async def create_program_studi(program_studi: ProgramStudiCreate, db: Session = Depends(get_db)):
    existing_program_studi = db.query(ProgramStudi).filter(ProgramStudi.name == program_studi.name).first()
    if existing_program_studi:
        raise HTTPException(status_code=400, detail="Program Studi dengan nama ini sudah ada")

    new_program_studi = ProgramStudi(**program_studi.dict())
    db.add(new_program_studi)
    db.commit()
    db.refresh(new_program_studi)
    return new_program_studi


@router.get("/{program_studi_id}", response_model=ProgramStudiRead)
async def read_program_studi(program_studi_id: int, db: Session = Depends(get_db)):
    program_studi = db.query(ProgramStudi).filter(ProgramStudi.id == program_studi_id).first()
    if not program_studi:
        raise HTTPException(status_code=404, detail="Program Studi tidak ditemukan")
    return program_studi


@router.get("/", response_model=List[ProgramStudiRead])
async def read_all_program_studi(db: Session = Depends(get_db)):
    return db.query(ProgramStudi).all()


@router.put("/{program_studi_id}", response_model=ProgramStudiRead)
async def update_program_studi(program_studi_id: int, updated_program_studi: ProgramStudiCreate, db: Session = Depends(get_db)):
    program_studi = db.query(ProgramStudi).filter(ProgramStudi.id == program_studi_id).first()
    if not program_studi:
        raise HTTPException(status_code=404, detail="Program Studi tidak ditemukan")

    for key, value in updated_program_studi.dict().items():
        setattr(program_studi, key, value)

    db.commit()
    db.refresh(program_studi)
    return program_studi


@router.delete("/{program_studi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program_studi(program_studi_id: int, db: Session = Depends(get_db)):
    program_studi = db.query(ProgramStudi).filter(ProgramStudi.id == program_studi_id).first()
    if not program_studi:
        raise HTTPException(status_code=404, detail="Program Studi tidak ditemukan")

    db.delete(program_studi)
    db.commit()
    return {"message": "Program Studi berhasil dihapus"}
