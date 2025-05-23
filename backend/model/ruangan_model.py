from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Integer
from typing import List

class Ruangan(Base):
    __tablename__ = "ruangan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kode_ruangan: Mapped[str] = mapped_column(String(20), nullable=False)
    nama_ruang: Mapped[str] = mapped_column(String(255), nullable=False)
    tipe_ruangan: Mapped[str] = mapped_column(String(1), nullable=False, default="T")

    kapasitas: Mapped[int] = mapped_column(Integer, nullable=False)
    alamat: Mapped[str] = mapped_column(String(500), nullable=True)
    gedung: Mapped[str] = mapped_column(String(50), nullable=True)
    group_code: Mapped[str] = mapped_column(String(20), nullable=True)

    # Relationships
    timetables: Mapped[List["TimeTable"]] = relationship(
        "TimeTable",
        back_populates="ruangan",
        cascade="all, delete-orphan"
    )

    temporary_timetables: Mapped[List["TemporaryTimeTable"]] = relationship(
        "TemporaryTimeTable",
        back_populates="new_ruangan"
    )

    def __repr__(self):
        return f"<Ruangan({self.kode_ruangan}, {self.nama_ruang}, kapasitas={self.kapasitas})>"
