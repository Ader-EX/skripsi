from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Date

class AcademicPeriods(Base):
    __tablename__ = "academic_periods"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tahun_ajaran: Mapped[str] = mapped_column(String(255), nullable=False)  
    semester: Mapped[int] = mapped_column(Integer, nullable=False)  
    start_date: Mapped[DateTime] = mapped_column(Date, nullable=False)
    end_date: Mapped[DateTime] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="academic_period")
    mahasiswa_timetables: Mapped[list["MahasiswaTimeTable"]] = relationship("MahasiswaTimeTable", back_populates="academic_period")

    def __repr__(self):
        return f"<AcademicPeriods(tahun_ajaran={self.tahun_ajaran}, semester={self.semester})>"
