
from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean

class Ruangan(Base):
    __tablename__ = "ruangan"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kode_ruangan: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    lokasi: Mapped[str] = mapped_column(String(255), nullable=False)

    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="ruangan")
