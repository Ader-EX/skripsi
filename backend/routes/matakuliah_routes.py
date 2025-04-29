from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from model.matakuliah_model import MataKuliah
from model.programstudi_model import ProgramStudi  

router = APIRouter()


class MataKuliahSimpleResponse(BaseModel):
    kodemk: str
    namamk: str

    class Config:
        orm_mode = True

# Pydantic Models
class MataKuliahBase(BaseModel):
    kodemk: str
    namamk: str
    sks: int
    smt : int
    kurikulum: str
    status_mk: str
    have_kelas_besar: bool
    program_studi_id: int 

    class Config:
        orm_mode = True

class MataKuliahCreate(BaseModel):
    kodemk: str
    namamk: str
    sks: int
    smt : int
    kurikulum: str
    status_mk: str
    tipe_mk: Optional[str] = "T"
    have_kelas_besar: bool
    program_studi_id: int
    # program_studi_name: Optional[str]

class MataKuliahRead(BaseModel):
    kodemk: str
    namamk: str
    sks: int
    smt : int
    kurikulum: str
    status_mk: str
    tipe_mk: str
    have_kelas_besar: bool
    program_studi_id: int
    program_studi_name: Optional[str]

    class Config:
        orm_mode = True

class PaginatedMataKuliah(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[MataKuliahRead]



from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from typing import List, Optional
from pydantic import BaseModel
from model.matakuliah_model import MataKuliah



class MataKuliahSimpleResponse(BaseModel):
    kodemk: str
    namamk: str
    tipe_mk: str
    have_kelas_besar: bool

    class Config:
        orm_mode = True

class PaginatedMatakuliahResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[MataKuliahSimpleResponse]




@router.get("/", response_model=PaginatedMataKuliah)
async def get_all_matakuliah(
    semester: Optional[str] = Query(None, description="Filter by semester"),
    kurikulum: Optional[str] = Query(None, description="Filter by kurikulum"),
    status_mk: Optional[str] = Query(None, description="Filter by status mk"),
    have_kelas_besar: Optional[str] = Query(None, description="Filter by have kelas besar"),
    program_studi_id: Optional[int] = Query(None, description="Filter by program studi id"),
    search: Optional[str] = Query(None, description="Search by kodemk or namamk"),
    page: int = Query(1, description="Page number", gt=0),
    page_size: int = Query(10, description="Page size", gt=0),
    db: Session = Depends(get_db),
):
    query = db.query(MataKuliah)
    

    if semester and semester != "Semua":
        try:
            semester = int(semester)
            query = query.filter(MataKuliah.smt == semester)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid semester value")

    if kurikulum:
        query = query.filter(MataKuliah.kurikulum.ilike(f"%{kurikulum}%"))
    if status_mk and status_mk != "Semua":
        query = query.filter(MataKuliah.status_mk == status_mk)
    if have_kelas_besar and have_kelas_besar != "Semua":
        query = query.filter(MataKuliah.have_kelas_besar == (have_kelas_besar.lower() == "true"))
    if program_studi_id and program_studi_id != 99:
        query = query.filter(MataKuliah.program_studi_id == program_studi_id)
    if search:
        query = query.filter((MataKuliah.kodemk.ilike(f"%{search}%")) | (MataKuliah.namamk.ilike(f"%{search}%")))
    
    total = query.count()
    mata_kuliah_list = query.offset((page - 1) * page_size).limit(page_size).all()
    
    result = [
        MataKuliahRead(
            kodemk=mk.kodemk,
            namamk=mk.namamk,
            sks=mk.sks,
            smt=mk.smt,
            kurikulum=mk.kurikulum,
            status_mk=mk.status_mk,
            have_kelas_besar=mk.have_kelas_besar,
            program_studi_id=mk.program_studi_id,
            tipe_mk = mk.tipe_mk,
            program_studi_name=db.query(ProgramStudi.name).filter(ProgramStudi.id == mk.program_studi_id).scalar()
        )
        for mk in mata_kuliah_list
    ]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": result
    }




@router.get("/get-matakuliah/names", response_model=PaginatedMatakuliahResponse)
async def get_matakuliah_names(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by kodemk or namamk"),
    page: int = Query(1, gt=0, description="Page number"),
    limit: int = Query(10, gt=0, le=100, description="Items per page")
):
    try:
        query = db.query(MataKuliah.kodemk, MataKuliah.namamk, MataKuliah.tipe_mk, MataKuliah.have_kelas_besar)

        if search:
            query = query.filter(
                (MataKuliah.kodemk.ilike(f"%{search}%")) | (MataKuliah.namamk.ilike(f"%{search}%"))
            )

        total = query.count()
        matakuliah_list = query.offset((page - 1) * limit).limit(limit).all()

        return {
            "total": total,
            "page": page,
            "page_size": limit,
            "data": [{"kodemk": mk.kodemk, "namamk": mk.namamk, "tipe_mk" : mk.tipe_mk, "have_kelas_besar" : mk.have_kelas_besar} for mk in matakuliah_list]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



# Create MataKuliah
@router.post("/", response_model=MataKuliahRead)
async def create_matakuliah(matakuliah: MataKuliahCreate, db: Session = Depends(get_db)):
    program_studi = db.query(ProgramStudi).filter(ProgramStudi.id == matakuliah.program_studi_id).first()
    if not program_studi:
        raise HTTPException(status_code=404, detail="Program Studi tidak ditemukan")

    new_matakuliah = MataKuliah(**matakuliah.dict())
    db.add(new_matakuliah)
    db.commit()
    db.refresh(new_matakuliah)

    return MataKuliahRead(**new_matakuliah.__dict__, program_studi_name=program_studi.name)

@router.get("/{matakuliah_id}", response_model=MataKuliahRead)
async def get_matakuliah(matakuliah_id: str, db: Session = Depends(get_db)):
    matakuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == matakuliah_id).first()
    if not matakuliah:
        raise HTTPException(status_code=404, detail="MataKuliah tidak ditemukan")

    program_studi_name = db.query(ProgramStudi.name).filter(ProgramStudi.id == matakuliah.program_studi_id).scalar()

    return MataKuliahRead(**matakuliah.__dict__, program_studi_name=program_studi_name)

@router.put("/{matakuliah_id}", response_model=MataKuliahRead)
async def update_matakuliah(matakuliah_id: str, updated_data: MataKuliahCreate, db: Session = Depends(get_db)):
    matakuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == matakuliah_id).first()
    if not matakuliah:
        raise HTTPException(status_code=404, detail="MataKuliah tidak ditemukan")

    program_studi = db.query(ProgramStudi).filter(ProgramStudi.id == updated_data.program_studi_id).first()
    if not program_studi:
        raise HTTPException(status_code=400, detail=f"ProgramStudi with ID {updated_data.program_studi_id} does not exist.")

    for key, value in updated_data.dict().items():
        setattr(matakuliah, key, value)

    db.commit()
    db.refresh(matakuliah)

    return MataKuliahRead(**matakuliah.__dict__, program_studi_name=program_studi.name)

@router.delete("/{kodemk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matakuliah(kodemk: str, db: Session = Depends(get_db)):
    matakuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == kodemk).first()
    if not matakuliah:
        raise HTTPException(status_code=404, detail="MataKuliah tidak ditemukan")

    db.delete(matakuliah)
    db.commit()
    return {
        "id" : kodemk,
        "detail" : "MataKuliah deleted successfully"

    }  



