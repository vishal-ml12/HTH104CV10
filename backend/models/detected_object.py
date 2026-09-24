from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.session import Base


class DetectedObject(Base):
    __tablename__ = "detected_objects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("waste_analysis.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    object_id = Column(String(50), nullable=False)
    material = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    box_x = Column(Float, nullable=False)
    box_y = Column(Float, nullable=False)
    box_width = Column(Float, nullable=False)
    box_height = Column(Float, nullable=False)
    stream = Column(String(50), nullable=False)  # "plastic", "glass", "metal", "paper", "organic", "review"
    status = Column(String(50), default="sorted", nullable=False)  # "sorted", "pending_review", "approved", "reclassified"
    reviewed_material = Column(String(50), nullable=True)
    contamination_score = Column(Float, default=0.0, nullable=False)
    contamination_category = Column(String(64), default="none", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    analysis = relationship("WasteAnalysis", back_populates="detected_objects")
