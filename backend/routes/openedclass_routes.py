from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, exists, func, or_, update
from sqlalchemy.orm import Session, joinedload
from routes.matakuliah_routes import PaginatedMatakuliahResponse
from model.timetable_model import TimeTable
from database import get_db
from model.openedclass_model import OpenedClass
from model.matakuliah_model import MataKuliah
from model.dosen_model import Dosen
from model.user_model import User
from model.dosenopened_model import openedclass_dosen
from typing import Dict, Any, Optional


from pydantic import BaseModel
from typing import List, Optional

class DosenSelection(BaseModel):
    id: int
    is_dosen_besar: bool  

class OpenedClassCreate(BaseModel):
    mata_kuliah_kodemk: str
    kelas: str
    kapasitas: int
    dosens: List[DosenSelection] 

class OpenedClassResponse(BaseModel):
    id: int
    mata_kuliah_kodemk: str
    kelas: str
    kapasitas: int
    dosens: List[DosenSelection] 

    class Config:
        orm_mode = True

router = APIRouter()



@router.post("/", response_model=OpenedClassResponse)
async def create_opened_class(data: OpenedClassCreate, db: Session = Depends(get_db)):
    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == data.mata_kuliah_kodemk).first()
    if not mata_kuliah:
        raise HTTPException(status_code=404, detail="Mata Kuliah tidak ditemukan")

    existing_class = db.query(OpenedClass).filter(
        OpenedClass.mata_kuliah_kodemk == data.mata_kuliah_kodemk,
        OpenedClass.kelas == data.kelas
    ).first()
    if existing_class:
        raise HTTPException(status_code=400, detail="Opened class dengan mata kuliah dan kelas ini sudah ada")

    if not data.dosens:
        raise HTTPException(status_code=400, detail="Minimal satu dosen harus dipilih")

    if mata_kuliah.tipe_mk == "T":
        if sum(1 for d in data.dosens if d.is_dosen_besar) > 1:
            raise HTTPException(status_code=400, detail="Hanya satu dosen dapat ditandai sebagai dosen besar.")
        if not any(d.is_dosen_besar for d in data.dosens):
            raise HTTPException(
                status_code=400,
                detail="Untuk kelas teori (dengan tipe MK T), salah satu dosen harus menjadi dosen besar."
            )

    user_used_prefs = [d for d in data.dosens if getattr(d, "used_preference", False)]
    if len(user_used_prefs) > 1:
        raise HTTPException(status_code=400, detail="Hanya satu dosen yang bisa dipilih sebagai used_preference")

    new_class = OpenedClass(
        mata_kuliah_kodemk=data.mata_kuliah_kodemk,
        kelas=data.kelas,
        kapasitas=data.kapasitas
    )
    db.add(new_class)
    db.flush()  

    dosen_ids = [dosen.id for dosen in data.dosens]
    dosens = db.query(Dosen).filter(Dosen.pegawai_id.in_(dosen_ids)).all()
    if not dosens:
        raise HTTPException(status_code=404, detail="No valid Dosen found")

    dosen_besar_id = next((dosen.id for dosen in data.dosens if dosen.is_dosen_besar), None)
    if not dosen_besar_id and mata_kuliah.tipe_mk == "T":
        from sqlalchemy import func
        dosen_appearance_counts = (
            db.query(openedclass_dosen.c.dosen_id, func.count(openedclass_dosen.c.opened_class_id).label("count"))
            .join(OpenedClass, OpenedClass.id == openedclass_dosen.c.opened_class_id)
            .filter(OpenedClass.mata_kuliah_kodemk == mata_kuliah.kodemk)
            .group_by(openedclass_dosen.c.dosen_id)
            .all()
        )
        dosen_appearance_dict = {d.dosen_id: d.count for d in dosen_appearance_counts}
        if dosen_appearance_dict:
            max_appearance = max(dosen_appearance_dict.values())
            top_dosens = [dosen_id for dosen_id, count in dosen_appearance_dict.items() if count == max_appearance]
            dosen_besar_id = top_dosens[0]
    if mata_kuliah.tipe_mk == "T" and not dosen_besar_id:
        raise HTTPException(
            status_code=400,
            detail="Untuk kelas teori (dengan tipe MK T), salah satu dosen harus menjadi dosen besar."
        )

    if len(user_used_prefs) == 1:
        chosen_used_pref_id = user_used_prefs[0].id
        if len(dosens) > 1 and chosen_used_pref_id == dosen_besar_id:
            raise HTTPException(status_code=400, detail="Dosen besar tidak dapat dipilih sebagai used_preference")
    else:
        if len(dosens) == 1:
            chosen_used_pref_id = dosens[0].pegawai_id
        else:
            from datetime import datetime
            sorted_dosens = sorted(
                dosens, 
                key=lambda d: d.tanggal_lahir if d.tanggal_lahir is not None else datetime.max,
                reverse=True
            )
            non_dosen_besar = [d for d in sorted_dosens if d.pegawai_id != dosen_besar_id]
            if not non_dosen_besar:
                raise HTTPException(status_code=400, detail="Tidak ada dosen yang valid untuk dipilih sebagai used_preference")
            chosen_used_pref_id = non_dosen_besar[0].pegawai_id

    dosen_entries = []
    for dosen in dosens:
        is_dosen_besar = (dosen.pegawai_id == dosen_besar_id)
        used_preference = (dosen.pegawai_id == chosen_used_pref_id)
        dosen_entries.append({
            "opened_class_id": new_class.id,
            "dosen_id": dosen.pegawai_id,
            "used_preference": used_preference,
            "is_dosen_besar": is_dosen_besar
        })

    db.execute(openedclass_dosen.insert(), dosen_entries)
    db.commit()
    db.refresh(new_class)

    return {
        "id": new_class.id,
        "mata_kuliah_kodemk": new_class.mata_kuliah_kodemk,
        "kelas": new_class.kelas,
        "kapasitas": new_class.kapasitas,
        "dosens": [
            {"id": dosen.pegawai_id, "is_dosen_besar": (dosen.pegawai_id == dosen_besar_id)}
            for dosen in dosens
        ],
    }
    
@router.get("/get-matakuliah/names", response_model=PaginatedMatakuliahResponse)
async def get_matakuliah_names(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by kodemk or namamk"),
    page: int = Query(1, gt=0, description="Page number"),
    limit: int = Query(10, gt=0, le=100, description="Items per page")
):
    try:
        query = (
            db.query(MataKuliah.kodemk, MataKuliah.namamk, MataKuliah.tipe_mk, MataKuliah.have_kelas_besar)
            .join(OpenedClass, MataKuliah.kodemk == OpenedClass.mata_kuliah_kodemk)  
            .filter(~exists().where(TimeTable.opened_class_id == OpenedClass.id))  
        )

       
        if search:
            query = query.filter(
                (MataKuliah.kodemk.ilike(f"%{search}%")) | 
                (MataKuliah.namamk.ilike(f"%{search}%"))
            )

       
        total = query.count()

      
        matakuliah_list = query.offset((page - 1) * limit).limit(limit).all()

        return {
            "total": total,
            "page": page,
            "page_size": limit,
            "data": [
                {
                    "kodemk": mk.kodemk,
                    "namamk": mk.namamk,
                    "tipe_mk": mk.tipe_mk,
                    "have_kelas_besar": mk.have_kelas_besar
                }
                for mk in matakuliah_list
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/get-all", response_model=Dict[str, Any])
async def get_opened_classes(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by mata kuliah name or kode mk"),
    no_timetable: bool = Query(False, description="Set to true to only return classes with no timetable entries")
):
    query = (
        db.query(OpenedClass)
            .join(OpenedClass.mata_kuliah)
            .join(MataKuliah.program_studi)
            .options(
                joinedload(OpenedClass.mata_kuliah).joinedload(MataKuliah.program_studi),
                joinedload(OpenedClass.dosens).joinedload(Dosen.user)
            )
    )

    if search:
        query = query.filter(
            or_(
                MataKuliah.namamk.ilike(f"%{search}%"),
                MataKuliah.kodemk.ilike(f"%{search}%")
            )
        )

    if no_timetable:
        query = query.filter(~OpenedClass.timetables.any())

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
                "tipe_mk": opened_class.mata_kuliah.tipe_mk,
                "program_studi": opened_class.mata_kuliah.program_studi.name
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

@router.put("/{opened_class_id}", response_model=OpenedClassResponse)
async def update_opened_class(opened_class_id: int, data: OpenedClassCreate, db: Session = Depends(get_db)):
  
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class tidak ditemukan")

    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == data.mata_kuliah_kodemk).first()
    if not mata_kuliah:
        raise HTTPException(status_code=404, detail="Mata Kuliah tidak ditemukan")

    if mata_kuliah.tipe_mk == "T":
        if sum(1 for d in data.dosens if d.is_dosen_besar) > 1:
            raise HTTPException(status_code=400, detail="Hanya satu dosen dapat ditandai sebagai dosen besar.")

    opened_class.mata_kuliah_kodemk = data.mata_kuliah_kodemk
    opened_class.kelas = data.kelas
    opened_class.kapasitas = data.kapasitas
    db.commit()
    db.refresh(opened_class)

    from sqlalchemy import delete
    db.execute(delete(openedclass_dosen).where(openedclass_dosen.c.opened_class_id == opened_class_id))

    dosen_ids = [dosen.id for dosen in data.dosens]
    dosens = db.query(Dosen).filter(Dosen.pegawai_id.in_(dosen_ids)).all()
    if not dosens:
        raise HTTPException(status_code=404, detail="No valid Dosen found")

    dosen_besar_id = next((dosen.id for dosen in data.dosens if dosen.is_dosen_besar), None)
    if not dosen_besar_id and mata_kuliah.tipe_mk == "T":
        from sqlalchemy import func
        dosen_appearance_counts = (
            db.query(openedclass_dosen.c.dosen_id, func.count(openedclass_dosen.c.opened_class_id).label("count"))
            .join(OpenedClass, OpenedClass.id == openedclass_dosen.c.opened_class_id)
            .filter(OpenedClass.mata_kuliah_kodemk == mata_kuliah.kodemk)
            .group_by(openedclass_dosen.c.dosen_id)
            .all()
        )
        dosen_appearance_dict = {d.dosen_id: d.count for d in dosen_appearance_counts}
        if dosen_appearance_dict:
            max_appearance = max(dosen_appearance_dict.values())
            top_dosens = [dosen_id for dosen_id, count in dosen_appearance_dict.items() if count == max_appearance]
            dosen_besar_id = top_dosens[0]
    if mata_kuliah.tipe_mk == "T" and not dosen_besar_id:
        raise HTTPException(
            status_code=400,
            detail="Untuk kelas teori (dengan tipe MK T), salah satu dosen harus menjadi dosen besar."
        )

    user_used_prefs = [d for d in data.dosens if getattr(d, "used_preference", False)]
    if len(user_used_prefs) > 1:
        raise HTTPException(status_code=400, detail="Hanya satu dosen yang bisa dipilih sebagai used_preference")

    if len(user_used_prefs) == 1:
        chosen_used_pref_id = user_used_prefs[0].id
        if len(dosens) > 1 and chosen_used_pref_id == dosen_besar_id:
            raise HTTPException(status_code=400, detail="Dosen besar tidak dapat dipilih sebagai used_preference")
    else:
        if len(dosens) == 1:
            chosen_used_pref_id = dosens[0].pegawai_id
        else:
            from datetime import datetime
            sorted_dosens = sorted(
                dosens, 
                key=lambda d: d.tanggal_lahir if d.tanggal_lahir is not None else datetime.max
            )
            non_dosen_besar = [d for d in sorted_dosens if d.pegawai_id != dosen_besar_id]
            if not non_dosen_besar:
                raise HTTPException(status_code=400, detail="Tidak ada dosen yang valid untuk dipilih sebagai used_preference")
            chosen_used_pref_id = non_dosen_besar[0].pegawai_id

    dosen_entries = []
    for dosen in dosens:
        is_dosen_besar = (dosen.pegawai_id == dosen_besar_id)
        used_preference = (dosen.pegawai_id == chosen_used_pref_id)
        dosen_entries.append({
            "opened_class_id": opened_class.id,
            "dosen_id": dosen.pegawai_id,
            "used_preference": used_preference,
            "is_dosen_besar": is_dosen_besar
        })

    db.execute(openedclass_dosen.insert(), dosen_entries)
    db.commit()

    return {
        "id": opened_class.id,
        "mata_kuliah_kodemk": opened_class.mata_kuliah_kodemk,
        "kelas": opened_class.kelas,
        "kapasitas": opened_class.kapasitas,
        "dosens": [{"id": dosen.pegawai_id, "is_dosen_besar": (dosen.pegawai_id == dosen_besar_id)} for dosen in dosens],
    }

@router.get("/{class_id}", response_model=Dict[str, Any])
async def get_opened_class(class_id: int, db: Session = Depends(get_db)):
    opened_class = (
        db.query(OpenedClass)
        .options(
            joinedload(OpenedClass.mata_kuliah),  
            joinedload(OpenedClass.dosens).joinedload(Dosen.user)
        )
        .filter(OpenedClass.id == class_id)
        .first()
    )

    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class tidak ditemukan")

    dosen_data = db.execute(
        openedclass_dosen.select().where(
            openedclass_dosen.c.opened_class_id == class_id
        )
    ).fetchall()

    dosen_besar_map = {row.dosen_id: row.is_dosen_besar for row in dosen_data}
    used_preference_map = {row.dosen_id: row.used_preference for row in dosen_data}

    return {
        "id": opened_class.id,
        "mata_kuliah_kodemk": opened_class.mata_kuliah.kodemk,
        "nama": opened_class.mata_kuliah.namamk,
        "tipe_mk": opened_class.mata_kuliah.tipe_mk,
        "have_kelas_besar": opened_class.mata_kuliah.have_kelas_besar, 
        "kelas": opened_class.kelas,
        "kapasitas": opened_class.kapasitas,
        "dosens": [
            {
                "pegawai_id": dosen.pegawai_id,
                "nama": dosen.nama,
                "is_dosen_besar": dosen_besar_map.get(dosen.pegawai_id, False),
                "used_preference": used_preference_map.get(dosen.pegawai_id, False) 
                
            }
            for dosen in opened_class.dosens
        ],
    }


@router.put("/{opened_class_id}/change-used-preference/{dosen_id}")
async def change_used_preference(opened_class_id: int, dosen_id: int, db: Session = Depends(get_db)):
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class tidak ditemukan")

    dosen = db.query(Dosen).filter(Dosen.pegawai_id == dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan")

    dosen_in_class = db.execute(
        openedclass_dosen.select().where(
            (openedclass_dosen.c.opened_class_id == opened_class_id) &
            (openedclass_dosen.c.dosen_id == dosen_id)
        )
    ).fetchone()

    if not dosen_in_class:
        raise HTTPException(status_code=400, detail="Dosen tidak di assign di kelas ini")

    db.execute(
        update(openedclass_dosen)
        .where(openedclass_dosen.c.opened_class_id == opened_class_id)
        .values(used_preference=False)
    )

    db.execute(
        update(openedclass_dosen)
        .where(
            (openedclass_dosen.c.opened_class_id == opened_class_id) &
            (openedclass_dosen.c.dosen_id == dosen_id)
        )
        .values(used_preference=True)
    )

    db.commit()
    return {"message": f"Dosen {dosen_id} sekarang jadi preferensi untuk kelas {opened_class_id}"}

@router.delete("/{opened_class_id}")
async def delete_opened_class(opened_class_id: int, db: Session = Depends(get_db)):
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class tidak ditemukan")

    db.execute(delete(TimeTable).where(TimeTable.opened_class_id == opened_class_id))

    db.execute(delete(openedclass_dosen).where(openedclass_dosen.c.opened_class_id == opened_class_id))

    db.delete(opened_class)

    db.commit()

    return {"message": f"Opened class {opened_class_id} dan timetable-nya berhasil dihapus"}