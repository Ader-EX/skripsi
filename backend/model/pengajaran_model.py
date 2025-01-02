from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Boolean

class Pengajaran(Base):
    __tablename__ = "pengajaran"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dosen_id: Mapped[int] = mapped_column(ForeignKey("dosen.id"), nullable=False)
    mk_id: Mapped[str] = mapped_column(ForeignKey("mata_kuliah.id"), nullable=False)
    is_dosen_kb: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    class_name: Mapped[str] = mapped_column(String(1), nullable=True)
    
    # Relationships
    dosen: Mapped["Dosen"] = relationship("Dosen", back_populates="pengajaran")
    mata_kuliah: Mapped["MataKuliah"] = relationship("MataKuliah", back_populates="pengajaran", foreign_keys=[mk_id])

    def __repr__(self):
        return f"<Pengajaran(id={self.id}, dosen_id={self.dosen_id}, mk_id={self.mk_id}, class={self.class_name})>"