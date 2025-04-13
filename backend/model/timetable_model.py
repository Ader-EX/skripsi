from typing import List
from model.timeslot_model import TimeSlot
from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship, object_session
from sqlalchemy import JSON, String, Integer, ForeignKey, Boolean
from sqlalchemy.ext.hybrid import hybrid_property

class TimeTable(Base):
    __tablename__ = "timetable"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    opened_class_id: Mapped[int] = mapped_column(ForeignKey("opened_class.id"), nullable=False)
    ruangan_id: Mapped[int] = mapped_column(ForeignKey("ruangan.id"), nullable=False)
    timeslot_ids: Mapped[List[int]] = mapped_column(JSON, nullable=False)  

    is_conflicted: Mapped[bool] = mapped_column(Boolean, default=False)
    kelas: Mapped[str] = mapped_column(String(10), nullable=False)  
    kapasitas: Mapped[int] = mapped_column(Integer, nullable=False, default=35)
    reason: Mapped[str] = mapped_column(String(255), nullable=True) 
    academic_period_id: Mapped[int] = mapped_column(ForeignKey("academic_periods.id"), nullable=False)
    kuota: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    placeholder: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    ruangan: Mapped["Ruangan"] = relationship("Ruangan", back_populates="timetables")
    academic_period: Mapped["AcademicPeriods"] = relationship("AcademicPeriods", back_populates="timetables")
    mahasiswa_timetable: Mapped[List["MahasiswaTimeTable"]] = relationship("MahasiswaTimeTable", back_populates="timetable")
    opened_class: Mapped["OpenedClass"] = relationship("OpenedClass", back_populates="timetables")
    temporary_timetables: Mapped[List["TemporaryTimeTable"]] = relationship(
        "TemporaryTimeTable",
        back_populates="timetable",
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def timeslots(self):
        session = object_session(self)
        if session is None:
            raise Exception("No session found for this object.")
        return session.query(TimeSlot).filter(TimeSlot.id.in_(self.timeslot_ids)).all()
