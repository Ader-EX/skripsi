from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey, DateTime, JSON
from datetime import datetime
from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey, DateTime, JSON
from datetime import datetime
from sqlalchemy.orm import object_session
from model.timeslot_model import TimeSlot


class TemporaryTimeTable(Base):
    __tablename__ = "temporary_timetable"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    timetable_id: Mapped[int] = mapped_column(ForeignKey("timetable.id"), nullable=False)
    timetable: Mapped["TimeTable"] = relationship("TimeTable", back_populates="temporary_timetables")

    new_ruangan_id: Mapped[int] = mapped_column(ForeignKey("ruangan.id"), nullable=True)
    new_ruangan: Mapped["Ruangan"] = relationship("Ruangan", back_populates="temporary_timetables")

    new_timeslot_ids: Mapped[list[int]] = mapped_column(JSON, nullable=True)
    new_day: Mapped[str] = mapped_column(String(10), nullable=True)

    change_reason: Mapped[str] = mapped_column(String(255), nullable=True)

    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_by: Mapped[str] = mapped_column(String(50), nullable=True)
    academic_period_id: Mapped[int] = mapped_column(ForeignKey("academic_periods.id"), nullable=False)

    def __repr__(self):
        return f"<TemporaryTimeTable(timetable_id={self.timetable_id}, new_ruangan_id={self.new_ruangan_id}, new_timeslot_ids={self.new_timeslot_ids}, new_day={self.new_day})>"
    
    @property
    def timeslots(self):
        session = object_session(self)
        if session is None:
            raise Exception("No session found for this object.")
        if not self.new_timeslot_ids:
            return []
        return session.query(TimeSlot).filter(TimeSlot.id.in_(self.new_timeslot_ids)).all()
