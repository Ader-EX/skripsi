from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey

class MahasiswaTimeTable(Base):
    __tablename__ = "mahasiswa_timetable"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mahasiswa_id: Mapped[int] = mapped_column(ForeignKey("mahasiswa.id"), nullable=False)
    timetable_id: Mapped[int] = mapped_column(ForeignKey("timetable.id"), nullable=False)
    academic_period_id: Mapped[int] = mapped_column(ForeignKey("academic_periods.id"), nullable=False)

    mahasiswa: Mapped["Mahasiswa"] = relationship("Mahasiswa", back_populates="mahasiswa_timetables")
    timetable: Mapped["TimeTable"] = relationship("TimeTable", back_populates="mahasiswa_timetable")
    academic_period: Mapped["AcademicPeriods"] = relationship("AcademicPeriods", back_populates="mahasiswa_timetables")

    def __repr__(self):
        return (
            f"<MahasiswaTimeTable(id={self.id}, mahasiswa_id={self.mahasiswa_id}, "
            f"timetable_id={self.timetable_id}, academic_period_id={self.academic_period_id})>"
        )
