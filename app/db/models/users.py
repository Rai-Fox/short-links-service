from sqlalchemy import Column, String

from db.models.base import Base
from core.security import get_password_hash


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    username = Column(String, primary_key=True, nullable=False)
    hashed_password = Column(String, nullable=False)
