from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey

class Mahasiswa(Base):
    __tablename__ = "mahasiswa"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    program_studi: Mapped[str] = mapped_column(String(255), nullable=False)
    tahun_masuk: Mapped[int] = mapped_column(Integer, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    sks_diambil: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="mahasiswa", uselist=False)
    mahasiswa_timetables: Mapped[list["MahasiswaTimeTable"]] = relationship("MahasiswaTimeTable", back_populates="mahasiswa")  # Add this line

    def __repr__(self):
        return f"<Mahasiswa(id={self.id}, program_studi={self.program_studi}, tahun_masuk={self.tahun_masuk})>"