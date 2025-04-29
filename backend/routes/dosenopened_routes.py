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
    is_dosen_kb: bool  
    kapasitas: int  
    kelas: str  



@router.post("/assign_dosen", status_code=status.HTTP_201_CREATED)
def assign_dosen_to_class(
    request: AssignDosenRequest,
    db: Session = Depends(get_db),
):
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == request.opened_class_id).first()
    dosen = db.query(Dosen).filter(Dosen.pegawai_id == request.dosen_id).first()

    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class tidak ditemukan")
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan")

    existing_lecturers = db.execute(
        openedclass_dosen.select().where(openedclass_dosen.c.opened_class_id == request.opened_class_id)
    ).fetchall()

    if len(existing_lecturers) >= request.kapasitas:
        raise HTTPException(status_code=400, detail="Class sudah penuh")

   
    db.execute(
        openedclass_dosen.insert().values(
            opened_class_id=request.opened_class_id,
            dosen_id=request.dosen_id,
            used_preference=False,
            is_dosen_besar=request.is_dosen_besar
        )
    )
    db.commit()

    updated_assignments = db.execute(
        openedclass_dosen.select().where(openedclass_dosen.c.opened_class_id == request.opened_class_id)
    ).fetchall()

    if updated_assignments:
        non_besar = [assignment for assignment in updated_assignments if not assignment.is_dosen_besar]
        if non_besar:
            chosen = sorted(non_besar, key=lambda a: a.dosen_id)[0]
        else:
            chosen = updated_assignments[0]

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
        "message": f"Dosen {dosen.pegawai_id} dijadwalkan untuk kelas {opened_class.kelas}.",
        "used_preference": True
    }
