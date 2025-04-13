from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from model.dosen_model import Dosen
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.ruangan_model import Ruangan
from database import get_db


router = APIRouter()



@router.get("/dashboard-stats",  response_model=Dict[str,Any], status_code=status.HTTP_200_OK)
async def get_dashboard_stats(db : Session = Depends(get_db)):
    mata_kuliah_count = db.query(func.count(MataKuliah.kodemk)).scalar()
    opened_class_count = db.query(func.count(OpenedClass.id)).scalar()
   
    ruangan_count = db.query(func.count(Ruangan.id)).scalar()
    dosen_count = db.query(func.count(Dosen.pegawai_id)).scalar()



    return {
        "mata_kuliah": {
            "count": mata_kuliah_count,
            "label": "Jumlah Mata Kuliah"
        },
        "mata_kuliah_dibuka": {
            "count": opened_class_count,
            "label": "Jumlah Mata Kuliah Dibuka"
        },
        "ruangan": {
            "count": ruangan_count,
            "label": "Jumlah Ruangan Terdaftar"
        },
        "dosen": {
            "count": dosen_count,
            "label": "Dosen Terdaftar"
        }
    }


