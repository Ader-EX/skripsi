from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Boolean, JSON

class Pengajaran(Base):
    __tablename__ = "pengajaran"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dosen_id: Mapped[int] = mapped_column(ForeignKey("dosen.id"), nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=[])
    opened_class_id: Mapped[int] = mapped_column(ForeignKey("opened_class.id"))

    # Relationships
    dosen: Mapped["Dosen"] = relationship("Dosen", back_populates="pengajaran")
    opened_class: Mapped["OpenedClass"] = relationship("OpenedClass")
    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="pengajaran")
    def __repr__(self):
        return f"<Pengajaran(id={self.id}, dosen_id={self.dosen_id}, mk_id={self.mk_id}, class={self.class_name})>"
