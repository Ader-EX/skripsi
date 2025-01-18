from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from model.openedclass_model import OpenedClass
from model.matakuliah_programstudi import MataKuliahProgramStudi
from pydantic import BaseModel

router = APIRouter()

# Pydantic Models
class OpenedClassBase(BaseModel):
    mata_kuliah_program_studi_id: int
    kelas: str
    kapasitas: int

class OpenedClassCreate(OpenedClassBase):
    pass

class OpenedClassRead(OpenedClassBase):
    id: int

    class Config:
        orm_mode = True


# Create OpenedClass
@router.post("/", response_model=OpenedClassRead, status_code=status.HTTP_201_CREATED)
async def create_opened_class(opened_class: OpenedClassCreate, db: Session = Depends(get_db)):
    # Check if MataKuliahProgramStudi exists
    mata_kuliah_program_studi = db.query(MataKuliahProgramStudi).filter(
        MataKuliahProgramStudi.id == opened_class.mata_kuliah_program_studi_id
    ).first()
    if not mata_kuliah_program_studi:
        raise HTTPException(status_code=404, detail="MataKuliahProgramStudi not found")

    # Create the OpenedClass
    new_opened_class = OpenedClass(**opened_class.dict())
    db.add(new_opened_class)
    db.commit()
    db.refresh(new_opened_class)
    return new_opened_class


# Read OpenedClass by ID
@router.get("/{opened_class_id}", response_model=OpenedClassRead)
async def read_opened_class(opened_class_id: int, db: Session = Depends(get_db)):
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="OpenedClass not found")
    return opened_class


# Read All OpenedClasses
@router.get("/", response_model=List[OpenedClassRead])
async def read_all_opened_classes(
    mata_kuliah_program_studi_id: Optional[int] = Query(None, description="Filter by MataKuliahProgramStudi ID"),
    db: Session = Depends(get_db),
):
    query = db.query(OpenedClass)
    if mata_kuliah_program_studi_id:
        query = query.filter(OpenedClass.mata_kuliah_program_studi_id == mata_kuliah_program_studi_id)
    return query.all()


# Update OpenedClass
@router.put("/{opened_class_id}", response_model=OpenedClassRead)
async def update_opened_class(opened_class_id: int, updated_opened_class: OpenedClassCreate, db: Session = Depends(get_db)):
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="OpenedClass not found")

    for key, value in updated_opened_class.dict().items():
        setattr(opened_class, key, value)

    db.commit()
    db.refresh(opened_class)
    return opened_class


# Delete OpenedClass
@router.delete("/{opened_class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opened_class(opened_class_id: int, db: Session = Depends(get_db)):
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="OpenedClass not found")

    db.delete(opened_class)
    db.commit()
    return {"message": "OpenedClass deleted successfully"}
