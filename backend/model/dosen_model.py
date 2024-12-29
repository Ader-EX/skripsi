from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean
class Dosen(Base):
    __tablename__ = "dosen"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    is_dosen_tambahan : Mapped[Boolean] = mapped_column(bool,default=False)
    user : Mapped["User"] = relationship("user", back_populates="dosen")