from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Integer,ForeignKey, DateTime, event, Boolean


class ListKelas(Base):
    __tablename__ = "list_kelas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pengajaran_id: Mapped[int] = mapped_column(ForeignKey("pengajaran.id"), nullable=False)
    ruangan_id: Mapped[int] = mapped_column(ForeignKey("ruangan.id"), nullable=False)
    timeslot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.id"), nullable=False)
    is_conflicted: Mapped[bool] = mapped_column(Boolean, default=False)
    kelas: Mapped[str] = mapped_column(String(10), nullable=False)  # E.g., A, B, C, D, ABCDE
    kapasitas: Mapped[int] = mapped_column(Integer, nullable=False, default=35)

    # Relationships
    pengajaran: Mapped["Pengajaran"] = relationship("Pengajaran", back_populates="list_kelas")
    ruangan: Mapped["Ruangan"] = relationship("Ruangan", back_populates="list_kelas")
    timeslot: Mapped["TimeSlot"] = relationship("TimeSlot", back_populates="list_kelas")
    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="kelas")
