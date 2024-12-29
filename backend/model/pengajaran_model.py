
from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean

class Pengajaran(Base):
    __tablename__ = "pengajaran"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dosen_id: Mapped[int] = mapped_column(ForeignKey("dosen.id"), nullable=False)
    mata_kuliah_id: Mapped[int] = mapped_column(ForeignKey("mata_kuliah.id"), nullable=False)

    dosen: Mapped["Dosen"] = relationship("Dosen", back_populates="pengajaran")
    mata_kuliah: Mapped["MataKuliah"] = relationship("MataKuliah", back_populates="pengajaran")
