from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean
class Mahasiswa(Base):
    __tablename__ = "mahasiswa"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    program_studi  : Mapped[str] = mapped_column(String(255), nullable=False)
    tahun_masuk : Mapped[int] = mapped_column(int, nullable=False)
    semester : Mapped[int] = mapped_column(int, nullable=False)
    sks_diambil : Mapped[int] = mapped_column(int, nullable=False)

    user: Mapped["User"] = relationship("user", back_populates="mahasiswa", uselist=False)
    mahasiswa_timetable : Mapped[list["MahasiswaTimeTable"]] =relationship("MahasiswaTimeTable", back_populates="mahasiswa")
    


