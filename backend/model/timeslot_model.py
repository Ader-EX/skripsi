from sqlalchemy import Column, Integer, String, Time, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from enum import Enum as PyEnum 

class DayEnum(str, PyEnum):  
    Senin = "Senin"
    Selasa = "Selasa"
    Rabu = "Rabu"
    Kamis = "Kamis"
    Jumat = "Jumat"
    Sabtu = "Sabtu"

class TimeSlot(Base):
    __tablename__ = "timeslot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day: Mapped[DayEnum] = mapped_column(Enum(DayEnum, name="day_enum", create_constraint=True), nullable=False)  
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)  
    start_time: Mapped[str] = mapped_column(Time, nullable=False)
    end_time: Mapped[str] = mapped_column(Time, nullable=False)

    # Relationships
    preferences: Mapped[list["Preference"]] = relationship("Preference", back_populates="timeslot")

    def __repr__(self):
        return f"<TimeSlot(day={self.day}, start_time={self.start_time}, end_time={self.end_time})>"
    