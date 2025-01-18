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
    dosen = db.query(Dosen).filter(Dosen.id == preference.dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")

    # Check if Timeslot exists
    timeslot = db.query(TimeSlot).filter(TimeSlot.id == preference.timeslot_id).first()
    if not timeslot:
        raise HTTPException(status_code=404, detail="Timeslot not found")

    # Create the preference
    new_preference = Preference(**preference.dict())
    db.add(new_preference)
    db.commit()
    db.refresh(new_preference)
    return new_preference


# Read Preference by ID
@router.get("/{preference_id}", response_model=PreferenceRead)
async def read_preference(preference_id: int, db: Session = Depends(get_db)):
    preference = db.query(Preference).filter(Preference.id == preference_id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")
    return preference


# Read All Preferences
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


# Update Preference
@router.put("/{preference_id}", response_model=PreferenceRead)
async def update_preference(preference_id: int, updated_preference: PreferenceCreate, db: Session = Depends(get_db)):
    preference = db.query(Preference).filter(Preference.id == preference_id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")

    # Update the preference fields
    for key, value in updated_preference.dict().items():
        setattr(preference, key, value)

    db.commit()
    db.refresh(preference)
    return preference


# Delete Preference
@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preference(preference_id: int, db: Session = Depends(get_db)):
    preference = db.query(Preference).filter(Preference.id == preference_id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")

    db.delete(preference)
    db.commit()
    return {"message": "Preference deleted successfully"}
