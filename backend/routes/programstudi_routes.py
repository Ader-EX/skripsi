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


# Routes

# Create ProgramStudi
@router.post("/", response_model=ProgramStudiRead, status_code=status.HTTP_201_CREATED)
async def create_program_studi(program_studi: ProgramStudiCreate, db: Session = Depends(get_db)):
    # Check if Program Studi with the same name already exists
    existing_program_studi = db.query(ProgramStudi).filter(ProgramStudi.name == program_studi.name).first()
    if existing_program_studi:
        raise HTTPException(status_code=400, detail="Program Studi with this name already exists")

    new_program_studi = ProgramStudi(**program_studi.dict())
    db.add(new_program_studi)
    db.commit()
    db.refresh(new_program_studi)
    return new_program_studi


# Read ProgramStudi by ID
@router.get("/{program_studi_id}", response_model=ProgramStudiRead)
async def read_program_studi(program_studi_id: int, db: Session = Depends(get_db)):
    program_studi = db.query(ProgramStudi).filter(ProgramStudi.id == program_studi_id).first()
    if not program_studi:
        raise HTTPException(status_code=404, detail="Program Studi not found")
    return program_studi


# Read All ProgramStudi
@router.get("/", response_model=List[ProgramStudiRead])
async def read_all_program_studi(db: Session = Depends(get_db)):
    return db.query(ProgramStudi).all()


# Update ProgramStudi
@router.put("/{program_studi_id}", response_model=ProgramStudiRead)
async def update_program_studi(program_studi_id: int, updated_program_studi: ProgramStudiCreate, db: Session = Depends(get_db)):
    program_studi = db.query(ProgramStudi).filter(ProgramStudi.id == program_studi_id).first()
    if not program_studi:
        raise HTTPException(status_code=404, detail="Program Studi not found")

    for key, value in updated_program_studi.dict().items():
        setattr(program_studi, key, value)

    db.commit()
    db.refresh(program_studi)
    return program_studi


# Delete ProgramStudi
@router.delete("/{program_studi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program_studi(program_studi_id: int, db: Session = Depends(get_db)):
    program_studi = db.query(ProgramStudi).filter(ProgramStudi.id == program_studi_id).first()
    if not program_studi:
        raise HTTPException(status_code=404, detail="Program Studi not found")

    db.delete(program_studi)
    db.commit()
    return {"message": "Program Studi deleted successfully"}
