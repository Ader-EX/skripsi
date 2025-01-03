from ..database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Boolean

class Pengajaran(Base):
    __tablename__ = "pengajaran"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dosen_id: Mapped[int] = mapped_column(ForeignKey("dosen.id"), nullable=False)
    mk_id: Mapped[int] = mapped_column(ForeignKey("mata_kuliah.id"), nullable=False)  # Use integer if primary key of MataKuliah is int
    is_dosen_kb: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    class_name: Mapped[str] = mapped_column(String(1), nullable=True)

    # Relationships
    dosen: Mapped["Dosen"] = relationship("Dosen", back_populates="pengajaran")
    mata_kuliah: Mapped["MataKuliah"] = relationship("MataKuliah", back_populates="pengajaran")

    def __repr__(self):
        return f"<Pengajaran(id={self.id}, dosen_id={self.dosen_id}, mk_id={self.mk_id}, class={self.class_name})>"
