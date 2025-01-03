from sqlalchemy import Column, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class TimeSlot(Base):
    __tablename__ = "timeslot"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Monday"
    start_time: Mapped[Time] = mapped_column(nullable=False)  # Start time
    end_time: Mapped[Time] = mapped_column(nullable=False)  # End time

    # Relationships
    preferences: Mapped[list["preference"]] = relationship("Preference", back_populates="timeslot")

    def __repr__(self):
        return f"<TimeSlot(day={self.day}, start_time={self.start_time}, end_time={self.end_time})>"
