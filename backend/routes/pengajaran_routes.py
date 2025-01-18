from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from pydantic import BaseModel
from model.pengajaran_model import Pengajaran

router = APIRouter()

# Pydantic Models
class PengajaranBase(BaseModel):
    dosen_id: int
    roles: List[str]  # Roles must be "DB" or "DK"
    opened_class_id: int

    class Config:
        orm_mode = True


class PengajaranCreate(PengajaranBase):
    pass


class PengajaranRead(PengajaranBase):
    id: int


# CRUD Routes
@router.post("/", response_model=PengajaranRead, status_code=status.HTTP_201_CREATED)
async def create_pengajaran(pengajaran: PengajaranCreate, db: Session = Depends(get_db)):
    # Validate roles
    if not all(role in {"DB", "DK"} for role in pengajaran.roles):
        raise HTTPException(status_code=400, detail="Invalid roles. Roles must be 'DB' or 'DK'.")

    # Check if 'DB' already exists for this opened_class_id
    if "DB" in pengajaran.roles:
        existing_db = db.query(Pengajaran).filter(
            Pengajaran.opened_class_id == pengajaran.opened_class_id,
            Pengajaran.roles.contains(["DB"])  # Check if any lecturer is already assigned as DB
        ).first()
        if existing_db:
            raise HTTPException(
                status_code=400, detail=f"Dosen Besar (DB) already exists for opened_class_id {pengajaran.opened_class_id}."
            )

    # Add the new Pengajaran entry
    new_pengajaran = Pengajaran(**pengajaran.dict())
    db.add(new_pengajaran)
    db.commit()
    db.refresh(new_pengajaran)
    return new_pengajaran


@router.get("/{pengajaran_id}", response_model=PengajaranRead)
async def read_pengajaran(pengajaran_id: int, db: Session = Depends(get_db)):
    pengajaran = db.query(Pengajaran).filter(Pengajaran.id == pengajaran_id).first()
    if not pengajaran:
        raise HTTPException(status_code=404, detail="Pengajaran not found")
    return pengajaran


@router.get("/", response_model=List[PengajaranRead])
async def get_all_pengajaran(
    opened_class_id: int = None, db: Session = Depends(get_db)
):
    query = db.query(Pengajaran)
    if opened_class_id:
        query = query.filter(Pengajaran.opened_class_id == opened_class_id)
    return query.all()


@router.put("/{pengajaran_id}", response_model=PengajaranRead)
async def update_pengajaran(pengajaran_id: int, updated_pengajaran: PengajaranCreate, db: Session = Depends(get_db)):
    pengajaran = db.query(Pengajaran).filter(Pengajaran.id == pengajaran_id).first()
    if not pengajaran:
        raise HTTPException(status_code=404, detail="Pengajaran not found")

    # Validate roles
    if not all(role in {"DB", "DK"} for role in updated_pengajaran.roles):
        raise HTTPException(status_code=400, detail="Invalid roles. Roles must be 'DB' or 'DK'.")

    # Check if 'DB' already exists for this opened_class_id
    if "DB" in updated_pengajaran.roles:
        existing_db = db.query(Pengajaran).filter(
            Pengajaran.opened_class_id == updated_pengajaran.opened_class_id,
            Pengajaran.roles.contains(["DB"]),
            Pengajaran.id != pengajaran_id  # Exclude the current record being updated
        ).first()
        if existing_db:
            raise HTTPException(
                status_code=400, detail=f"Dosen Besar (DB) already exists for opened_class_id {updated_pengajaran.opened_class_id}."
            )

    # Update fields
    for key, value in updated_pengajaran.dict().items():
        setattr(pengajaran, key, value)

    db.commit()
    db.refresh(pengajaran)
    return pengajaran


@router.delete("/{pengajaran_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pengajaran(pengajaran_id: int, db: Session = Depends(get_db)):
    pengajaran = db.query(Pengajaran).filter(Pengajaran.id == pengajaran_id).first()
    if not pengajaran:
        raise HTTPException(status_code=404, detail="Pengajaran not found")

    db.delete(pengajaran)
    db.commit()
    return {"message": "Pengajaran deleted successfully"}
