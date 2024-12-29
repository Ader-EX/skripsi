from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fullname: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False) 
    role: Mapped[str] = mapped_column(String(255), nullable=False)

    mahasiswa : Mapped["Mahasiswa"] = relationship("mahasiswa", back_populates="user", uselist=False)
    dosen: Mapped["Dosen"] = relationship("dosen", back_populates="user", uselist=False)
    admin: Mapped["Admin"] = relationship("admin", back_populates="user", uselist=False)


