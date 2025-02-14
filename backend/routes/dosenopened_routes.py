from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, Optional, List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, validator

from database import get_db
from model.dosen_model import Dosen
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.ruangan_model import Ruangan
from model.user_model import User
from model.dosenopened_model import openedclass_dosen



router = APIRouter()




class AssignDosenRequest(BaseModel):
    dosen_id: int
    opened_class_id: int
    is_dosen_kb: bool  # Boolean to determine if the lecturer is a 'Dosen Besar'
    kapasitas: int  # Capacity of the class
    kelas: str  # Class name (A, B, C, etc.)

@router.post("/assign_dosen", status_code=status.HTTP_201_CREATED)
def assign_dosen_to_class(
    request: AssignDosenRequest,
    db: Session = Depends(get_db),
):
    """
    Assign a Dosen to an Opened Class with dynamic used_preference calculation.
    """

    # Fetch the class and dosen
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == request.opened_class_id).first()
    dosen = db.query(Dosen).filter(Dosen.pegawai_id == request.dosen_id).first()

    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class not found")
    
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")

    # Count existing lecturers in the class
    existing_lecturers = db.execute(
        openedclass_dosen.select().where(openedclass_dosen.c.opened_class_id == request.opened_class_id)
    ).fetchall()

    if len(existing_lecturers) >= request.kapasitas:
        raise HTTPException(status_code=400, detail="Class is already at full capacity")

    # Get all assigned lecturers
    existing_dosen = db.query(Dosen).filter(Dosen.pegawai_id.in_([row.dosen_id for row in existing_lecturers])).all()

    # Sort by age (older first)
    existing_dosen_sorted = sorted(existing_dosen, key=lambda d: d.tanggal_lahir or 0, reverse=True)

    # Check if any older lecturer has already used preference
    preference_already_used = any(d.tanggal_lahir and (d.tanggal_lahir < dosen.tanggal_lahir) for d in existing_dosen_sorted)

    # Determine used_preference
    used_preference = False if request.is_dosen_kb else not preference_already_used

    # Insert the lecturer into the class
    db.execute(
        openedclass_dosen.insert().values(
            opened_class_id=request.opened_class_id,
            dosen_id=request.dosen_id,
            used_preference=used_preference
        )
    )

    db.commit()
    return {
        "message": f"Dosen {dosen.pegawai_id} assigned to class {opened_class.kelas}, used_preference: {used_preference}"
    }