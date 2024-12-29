from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean


class MataKuliah(Base):
    __tablename__ = "mata_kuliah"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kode: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    sks: Mapped[int] = mapped_column(int, nullable=False)

    pengajaran: Mapped[list["Pengajaran"]] = relationship("Pengajaran", back_populates="mata_kuliah")
    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="mata_kuliah")
