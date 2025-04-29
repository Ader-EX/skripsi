from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from model.preference_model import Preference
from model.dosen_model import Dosen
from model.timeslot_model import TimeSlot
from pydantic import BaseModel, Field

router = APIRouter()

# Pydantic Models
class PreferenceBase(BaseModel):
    dosen_id: int = Field(..., description="ID of the lecturer (Dosen)")
    timeslot_id: int = Field(..., description="ID of the preferred timeslot")
    is_special_needs: Optional[bool] = Field(False, description="Indicates if this is for special needs")
    is_high_priority: Optional[bool] = Field(False, description="Indicates if this preference is high priority")
    reason: Optional[str] = Field(None, description="Reason for the preference")

class PreferenceCreate(PreferenceBase):
    pass

class PreferenceRead(PreferenceBase):
    id: int

    class Config:
        orm_mode = True


# Create Preference
@router.post("/", response_model=PreferenceRead, status_code=status.HTTP_201_CREATED)
async def create_preference(preference: PreferenceCreate, db: Session = Depends(get_db)):
    # Check if Dosen exists
    dosen = db.query(Dosen).filter(Dosen.pegawai_id == preference.dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")

    # Check if Timeslot exists
    timeslot = db.query(TimeSlot).filter(TimeSlot.id == preference.timeslot_id).first()
    if not timeslot:
        raise HTTPException(status_code=404, detail="Timeslot not found")
   
    if dosen.jabatan and dosen.jabatan.strip() and timeslot.day_index == 0:
        raise HTTPException(
            status_code=400,
            detail="Dosen dengan jabatan tidak bisa memilih timeslot dengan hari Senin",
        )

    new_preference = Preference(**preference.dict())
    db.add(new_preference)
    db.commit()
    db.refresh(new_preference)
    return new_preference





@router.get("/{preference_id}", response_model=PreferenceRead)
async def read_preference(preference_id: int, db: Session = Depends(get_db)):
    preference = db.query(Preference).filter(Preference.id == preference_id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")
    return preference

@router.get("/dosen/{dosen_id}", response_model=List[PreferenceRead])
async def read_dosen_preference( dosen_id: int, db: Session = Depends(get_db)):
    preferences = db.query(Preference).filter(Preference.dosen_id == dosen_id).all()
    return preferences

@router.get("/dosen/{user_id}/has-preference", response_model=bool)
async def dosen_has_preference(user_id: int, db: Session = Depends(get_db)):
    preference = db.query(Preference).filter(Preference.dosen_id == user_id).first()
    if not preference:
        return False
    return True


@router.get("/", response_model=List[PreferenceRead])
async def read_all_preferences(
    dosen_id: Optional[int] = None,
    timeslot_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Preference)
    if dosen_id:
        query = query.filter(Preference.dosen_id == dosen_id)
    if timeslot_id:
        query = query.filter(Preference.timeslot_id == timeslot_id)
    return query.all()


@router.put("/set-special-needs/{dosen_id}")
async def toggle_special_needs(dosen_id: int, db: Session = Depends(get_db)):
    preferences = db.query(Preference).filter(Preference.dosen_id == dosen_id).all()

    if not preferences:
        raise HTTPException(status_code=404, detail="preferensi tidak ditemukan untuk dosen ini")

    current_status = any(pref.is_special_needs for pref in preferences)
    new_status = not current_status

    db.query(Preference).filter(Preference.dosen_id == dosen_id).update(
        {"is_special_needs": new_status}, synchronize_session=False
    )

    db.commit()
    return {
        "message": f"Special needs preferences diubah menjadi {new_status} untuk dosen {dosen_id}"
    }



@router.put("/{preference_id}", response_model=PreferenceRead)
async def update_preference(preference_id: int, updated_preference: PreferenceCreate, db: Session = Depends(get_db)):
    preference = db.query(Preference).filter(Preference.id == preference_id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="Preference tidak ditemukan")

    for key, value in updated_preference.dict().items():
        setattr(preference, key, value)

    db.commit()
    db.refresh(preference)
    return preference


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preference(preference_id: int, db: Session = Depends(get_db)):
    preference = db.query(Preference).filter(Preference.id == preference_id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="Preference tidak ditemukan")

    db.delete(preference)
    db.commit()
    return {"message": "Preference berhasil dihapus"}
