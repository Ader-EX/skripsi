from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey, Boolean, Table, Column


metadata = Base.metadata  # Use the same metadata as your ORM models



class MataKuliah(Base):
    __tablename__ = "mata_kuliah"

    kodemk: Mapped[str] = mapped_column(String(20), primary_key=True)
    namamk: Mapped[str] = mapped_column(String(255), nullable=False)
    sks: Mapped[int] = mapped_column(Integer, nullable=False)
    smt: Mapped[int] = mapped_column(Integer, nullable=False)
    kurikulum: Mapped[str] = mapped_column(String(20), nullable=False)
    status_mk: Mapped[str] = mapped_column(String(1), nullable=False)
    have_kelas_besar: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tipe_mk: Mapped[int] = mapped_column(Integer, nullable=False)

    program_studi_associations: Mapped[list["MataKuliahProgramStudi"]] = relationship("MataKuliahProgramStudi", back_populates="mata_kuliah")
    opened_classes: Mapped[list["OpenedClass"]] = relationship("OpenedClass", back_populates="mata_kuliah")  # Keep this for direct relationships

    def __repr__(self):
        return f"<MataKuliah(kodemk={self.kodemk}, namamk={self.namamk})>"
