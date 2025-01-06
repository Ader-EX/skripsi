from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey


class OpenedClass(Base):
    __tablename__ = "opened_class"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kodemk: Mapped[str] = mapped_column(ForeignKey("mata_kuliah.kodemk"), nullable=False)
    program_studi: Mapped[str] = mapped_column(String(10), nullable=False)  # E.g., "SIF", "SI", etc.
    kelas: Mapped[str] = mapped_column(String(10), nullable=False)  # E.g., "A", "B", "C", etc.
    kapasitas: Mapped[int] = mapped_column(Integer, nullable=False)  # Capacity of the class

    # Relationships
    mata_kuliah: Mapped["MataKuliah"] = relationship("MataKuliah", back_populates="opened_classes")
    pengajaran: Mapped[list["Pengajaran"]] = relationship("Pengajaran", back_populates="opened_class")


def __repr__(self):
    return f"<OpenedClass(id={self.id}, kodemk={self.kodemk}, program_studi={self.program_studi}, kelas={self.kelas})>"
