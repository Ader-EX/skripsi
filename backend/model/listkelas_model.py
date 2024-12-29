from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean


class ListKelas(Base):
    __tablename__ = "list_kelas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kode_kelas: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nama_kelas: Mapped[str] = mapped_column(String(255), nullable=False)

    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="kelas")

