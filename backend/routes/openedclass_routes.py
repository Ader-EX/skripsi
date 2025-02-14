from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from database import get_db
from model.openedclass_model import OpenedClass
from model.matakuliah_model import MataKuliah
from model.dosen_model import Dosen
from model.user_model import User
from typing import Dict, Any, Optional

router = APIRouter()

@router.get("/get-all", response_model=Dict[str, Any])  # ✅ Fix response model
async def get_opened_classes(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by mata kuliah name or kode mk")
):
    query = (
        db.query(OpenedClass)
        .join(OpenedClass.mata_kuliah)
        .options(
            joinedload(OpenedClass.mata_kuliah),  # Load mata kuliah details
            joinedload(OpenedClass.dosens).joinedload(Dosen.user)  # Load dosens and their user info
        )
    )

    if search:
        query = query.filter(
            or_(
                MataKuliah.namamk.ilike(f"%{search}%"),
                MataKuliah.kodemk.ilike(f"%{search}%")
            )
        )

    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit

    opened_classes = query.offset((page - 1) * limit).limit(limit).all()

    result = []
    for opened_class in opened_classes:
        result.append({
            "id": opened_class.id,
            "mata_kuliah": {
                "kode": opened_class.mata_kuliah.kodemk,
                "nama": opened_class.mata_kuliah.namamk,
                "sks": opened_class.mata_kuliah.sks,
                "semester": opened_class.mata_kuliah.smt,
                "tipe_mk": opened_class.mata_kuliah.tipe_mk  # ✅ Include Tipe MK
            },
            "kelas": opened_class.kelas,
            "kapasitas": opened_class.kapasitas,
            "dosens": [
                {
                    "id": dosen.pegawai_id,
                    "fullname": dosen.nama, 
                    "nip": dosen.user.nim_nip,
                    "jabatan": dosen.jabatan
                }
                for dosen in opened_class.dosens
            ]
        })

    return dict(
        page=page,
        limit=limit,
        total_pages=total_pages,
        total_records=total_records,
        data=result
    )
