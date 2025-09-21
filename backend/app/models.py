from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.db import Base

class FlaggedAccount(Base):
    __tablename__ = "flagged_accounts"
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(32), index=True)
    handle = Column(String(256), index=True)
    display_name = Column(String(512))
    description = Column(Text, nullable=True)
    metadata_hash = Column(String(128), nullable=True)
    risk_score = Column(Float, default=0.0)
    reasons = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
