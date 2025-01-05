from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Boolean

class TimeTable(Base):
    __tablename__ = "timetable"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kelas_id: Mapped[int] = mapped_column(ForeignKey("list_kelas.id"), nullable=False)
    pengajaran_id: Mapped[int] = mapped_column(ForeignKey("pengajaran.id"), nullable=False)
    ruangan_id: Mapped[int] = mapped_column(ForeignKey("ruangan.id"), nullable=False)
    timeslot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.id"), nullable=False)
    is_conflicted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    kelas: Mapped["ListKelas"] = relationship("ListKelas", back_populates="timetables")
    ruangan: Mapped["Ruangan"] = relationship("Ruangan", back_populates="timetables")
    timeslot: Mapped["TimeSlot"] = relationship("TimeSlot", back_populates="timetables")
    mahasiswa_timetable: Mapped[list["MahasiswaTimeTable"]] = relationship("MahasiswaTimeTable", back_populates="timetable")

    def __repr__(self):
        return f"<TimeTable(kelas_id={self.kelas_id}, ruangan={self.ruangan_id}, timeslot={self.timeslot_id})>"