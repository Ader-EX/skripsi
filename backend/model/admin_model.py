from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, event, Boolean
class Admin(Base):
    __tablename__ = "admin"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    staff_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="admin")