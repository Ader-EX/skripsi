from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Preference(Base):
    __tablename__ = "preference"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dosen_id: Mapped[int] = mapped_column(ForeignKey("dosen.pegawai_id"), nullable=False)
    timeslot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.id"), nullable=False)
    is_special_needs: Mapped[bool] = mapped_column(Boolean, default=False)
    is_high_priority: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    dosen: Mapped["Dosen"] = relationship("Dosen", back_populates="preferences")
    timeslot: Mapped["Timeslot"] = relationship("TimeSlot", back_populates="preferences")

    def __repr__(self):
        return f"<Preference(dosen_id={self.dosen_id}, timeslot_id={self.timeslot_id})>"
