from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean

class TimeTable(Base):
    __tablename__ = "timetable"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pengajaran_id: Mapped[int] = mapped_column(ForeignKey("pengajaran.id"), nullable=False)
    ruangan_id: Mapped[int] = mapped_column(ForeignKey("ruangan.id"), nullable=False)
    timeslot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.id"), nullable=False)
    is_conflicted: Mapped[bool] = mapped_column(Boolean, default=False)
    kelas: Mapped[str] = mapped_column(String(10), nullable=False)  # E.g., A, B, C, D
    kapasitas: Mapped[int] = mapped_column(Integer, nullable=False, default=35)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)  # Optional field for conflict reasons
    academic_period_id: Mapped[int] = mapped_column(ForeignKey("academic_periods.id"), nullable=False)
    kuota : Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    placeholder: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    pengajaran: Mapped["Pengajaran"] = relationship("Pengajaran", back_populates="timetables")
    ruangan: Mapped["Ruangan"] = relationship("Ruangan", back_populates="timetables")
    timeslot: Mapped["TimeSlot"] = relationship("TimeSlot", back_populates="timetables")
    academic_period: Mapped["AcademicPeriods"] = relationship("AcademicPeriods", back_populates="timetables")
    mahasiswa_timetable: Mapped[list["MahasiswaTimeTable"]] = relationship("MahasiswaTimeTable", back_populates="timetable")

    def __repr__(self):
        return (
            f"<TimeTable(pengajaran_id={self.pengajaran_id}, ruangan={self.ruangan_id}, "
            f"timeslot={self.timeslot_id}, kapasitas={self.kapasitas}, academic_period={self.academic_period_id})>"
        )
