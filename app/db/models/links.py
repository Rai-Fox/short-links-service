from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.sql import func

from db.models.base import Base


class Link(Base):
    __tablename__ = "links"
    __table_args__ = {"extend_existing": True}

    link_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_code = Column(String, primary_key=True, index=True, nullable=False)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)  # Nullable for non-authenticated users
    clicks = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)  # 1 for active, 0 for inactive
