from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from model.academicperiod_model import AcademicPeriods
from pydantic import BaseModel
from datetime import date
from model.timetable_model import TimeTable

router = APIRouter()

# Pydantic Models
class AcademicPeriodBase(BaseModel):
    tahun_ajaran: int
    semester: int
    start_date: date
    end_date: date
    is_active: bool = True

class AcademicPeriodCreate(AcademicPeriodBase):
    pass

class AcademicPeriodRead(AcademicPeriodBase):
    id: int

    class Config:
        orm_mode = True


# Routes
@router.post("/", response_model=AcademicPeriodRead, status_code=status.HTTP_201_CREATED)
async def create_academic_period(
    academic_period: AcademicPeriodCreate, db: Session = Depends(get_db)
):
    # Validate dates
    if academic_period.start_date >= academic_period.end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be earlier than end date"
        )

    # Ensure only one active period exists
    if academic_period.is_active:
        active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
        if active_period:
            raise HTTPException(
                status_code=400,
                detail="Only one academic period can be active at a time"
            )

    # Create a new academic period
    new_period = AcademicPeriods(**academic_period.dict())
    db.add(new_period)
    db.commit()
    db.refresh(new_period)
    return new_period

@router.put("/academic-period/{academic_period_id}/activate", status_code=status.HTTP_200_OK)
async def activate_academic_period(academic_period_id: int, db: Session = Depends(get_db)):
    # Fetch the academic period to activate
    academic_period = db.query(AcademicPeriods).filter(AcademicPeriods.id == academic_period_id).first()
    if not academic_period:
        raise HTTPException(status_code=404, detail="Academic period not found")

    # Check if the period is already active
    if academic_period.is_active:
        raise HTTPException(status_code=400, detail="This academic period is already active")

    # Deactivate the current active period
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if active_period:
        active_period.is_active = False
        db.commit()

    # Activate the new academic period
    academic_period.is_active = True
    db.commit()

    # Update timetables associated with the previous active period
    if active_period:
        timetables = db.query(TimeTable).filter(TimeTable.academic_period_id == active_period.id).all()
        for timetable in timetables:
            timetable.is_conflicted = True  # Example: Mark timetables as inactive or conflicted
        db.commit()

    return {"message": f"Academic period {academic_period.tahun_ajaran}/{academic_period.semester} is now active"}


@router.get("/", response_model=List[AcademicPeriodRead])
async def get_all_academic_periods(db: Session = Depends(get_db)):
    return db.query(AcademicPeriods).all()


@router.get("/active", status_code=status.HTTP_200_OK)
async def get_active_academic_period(db: Session = Depends(get_db)):
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    
    if not active_period:
        raise HTTPException(status_code=404, detail="No active academic period found")

    return {
        "semester": active_period.semester,
        "tahun_ajaran": active_period.tahun_ajaran
    }


@router.get("/{academic_period_id}", response_model=AcademicPeriodRead)
async def get_academic_period_by_id(academic_period_id: int, db: Session = Depends(get_db)):
    academic_period = db.query(AcademicPeriods).filter(AcademicPeriods.id == academic_period_id).first()
    if not academic_period:
        raise HTTPException(status_code=404, detail="Academic period not found")
    return academic_period


@router.put("/{academic_period_id}", response_model=AcademicPeriodRead)
async def update_academic_period(
    academic_period_id: int,
    updated_period: AcademicPeriodCreate,
    db: Session = Depends(get_db)
):
    academic_period = db.query(AcademicPeriods).filter(AcademicPeriods.id == academic_period_id).first()
    if not academic_period:
        raise HTTPException(status_code=404, detail="Academic period not found")

    # Validate dates
    if updated_period.start_date >= updated_period.end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be earlier than end date"
        )

    # Ensure only one active period exists
    if updated_period.is_active:
        active_period = db.query(AcademicPeriods).filter(
            AcademicPeriods.is_active == True, AcademicPeriods.id != academic_period_id
        ).first()
        if active_period:
            raise HTTPException(
                status_code=400,
                detail="Only one academic period can be active at a time"
            )

    for key, value in updated_period.dict().items():
        setattr(academic_period, key, value)

    db.commit()
    db.refresh(academic_period)
    return academic_period




@router.delete("/{academic_period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_academic_period(academic_period_id: int, db: Session = Depends(get_db)):
    academic_period = db.query(AcademicPeriods).filter(AcademicPeriods.id == academic_period_id).first()
    if not academic_period:
        raise HTTPException(status_code=404, detail="Academic period not found")

    db.delete(academic_period)
    db.commit()
    return {"message": "Academic period deleted successfully"}


