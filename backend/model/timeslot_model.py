from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean

class TimeSlot(Base):
    __tablename__ = "timeslot"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hari: Mapped[str] = mapped_column(String(50), nullable=False)  # Example: "Monday"
    waktu_mulai: Mapped[DateTime] = mapped_column(DateTime,nullable=False)  # Start time
    waktu_selesai: Mapped[DateTime] = mapped_column(DateTime,nullable=False)  # End time

    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="timeslot")
    preferences: Mapped[list["Preference"]] = relationship("Preference", back_populates="timeslot")