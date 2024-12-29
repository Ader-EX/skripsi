from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Preference(Base):
    __tablename__ = "preference"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mahasiswa_id: Mapped[int] = mapped_column(ForeignKey("mahasiswa.id"), nullable=False)
    preferred_timeslot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.id"), nullable=False)

    mahasiswa: Mapped["Mahasiswa"] = relationship("Mahasiswa", back_populates="preferences")
    timeslot: Mapped["TimeSlot"] = relationship("TimeSlot")



