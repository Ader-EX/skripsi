from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Boolean, String


class MahasiswaTimeTable(Base):
    __tablename__ = "mahasiswa_timetable"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mahasiswa_id: Mapped[int] = mapped_column(ForeignKey("mahasiswa.id"), nullable=False)
    timetable_id: Mapped[int] = mapped_column(ForeignKey("timetable.id"), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    tahun_ajaran: Mapped[int] = mapped_column(Integer, nullable=False)
    total_sks : Mapped[int] = mapped_column(Integer, nullable=False, default = 0)

    mahasiswa: Mapped["Mahasiswa"] = relationship("Mahasiswa", back_populates="mahasiswa_timetables")
    timetable: Mapped["TimeTable"] = relationship("TimeTable", back_populates="mahasiswa_timetable")

    def __repr__(self):
        return (
        f"<MahasiswaTimeTable(id={self.id}, mahasiswa_id={self.mahasiswa_id}, "
        f"timetable_id={self.timetable_id}, semester={self.semester}, tahun_ajaran={self.tahun_ajaran}, "
        f"status={'Active' if self.status else 'Inactive'})>"
    )