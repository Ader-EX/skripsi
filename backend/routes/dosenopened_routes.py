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
    Assign a Dosen to an Opened Class, then adjust used_preference so that exactly one lecturer (preferably a dosen kecil)
    is marked as used_preference for that class.
    """
    # Fetch the opened class and dosen
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == request.opened_class_id).first()
    dosen = db.query(Dosen).filter(Dosen.pegawai_id == request.dosen_id).first()

    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class not found")
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")

    # Check current capacity
    existing_lecturers = db.execute(
        openedclass_dosen.select().where(openedclass_dosen.c.opened_class_id == request.opened_class_id)
    ).fetchall()

    if len(existing_lecturers) >= request.kapasitas:
        raise HTTPException(status_code=400, detail="Class is already at full capacity")

    # Insert the lecturer with a default used_preference of False.
    # Also assume the request contains a boolean flag 'is_dosen_besar'
    db.execute(
        openedclass_dosen.insert().values(
            opened_class_id=request.opened_class_id,
            dosen_id=request.dosen_id,
            used_preference=False,
            is_dosen_besar=request.is_dosen_besar
        )
    )
    db.commit()

    # Recalculate used_preference for the class to ensure exactly one is marked.
    updated_assignments = db.execute(
        openedclass_dosen.select().where(openedclass_dosen.c.opened_class_id == request.opened_class_id)
    ).fetchall()

    if updated_assignments:
        # Prefer a dosen kecil (i.e., where is_dosen_besar is False)
        non_besar = [assignment for assignment in updated_assignments if not assignment.is_dosen_besar]
        if non_besar:
            # If there's exactly one non-besar, choose that; if more, pick by some tie-breaker (e.g. lower dosen_id)
            chosen = sorted(non_besar, key=lambda a: a.dosen_id)[0]
        else:
            # Otherwise, if all are dosen besar, pick the first one
            chosen = updated_assignments[0]

        # Reset all to False, then update the chosen one to True.
        db.execute(
            openedclass_dosen.update().where(
                openedclass_dosen.c.opened_class_id == request.opened_class_id
            ).values(used_preference=False)
        )
        db.execute(
            openedclass_dosen.update().where(
                (openedclass_dosen.c.opened_class_id == request.opened_class_id) &
                (openedclass_dosen.c.dosen_id == chosen.dosen_id)
            ).values(used_preference=True)
        )
        db.commit()

    return {
        "message": f"Dosen {dosen.pegawai_id} assigned to class {opened_class.kelas}.",
        "used_preference": True  # Now ensured to have exactly one used_preference.
    }
