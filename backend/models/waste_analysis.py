from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.session import Base


class WasteAnalysis(Base):
    __tablename__ = "waste_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), unique=True, index=True, nullable=True)
    material = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    contamination_level = Column(String(50), nullable=False)
    contamination_percentage = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    recycling_yield = Column(Float, nullable=False)
    recommendation = Column(String(255), nullable=False)
    total_objects = Column(Integer, default=1, nullable=False)
    plastic_count = Column(Integer, default=0, nullable=False)
    glass_count = Column(Integer, default=0, nullable=False)
    metal_count = Column(Integer, default=0, nullable=False)
    paper_count = Column(Integer, default=0, nullable=False)
    organic_count = Column(Integer, default=0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    mode = Column(String(30), default="REAL_YOLO", nullable=False)
    image_name = Column(String(255), nullable=True)
    recommendation_reason = Column(String(500), nullable=True)
    processing_route = Column(String(64), nullable=True)
    input_mass_kg = Column(Float, default=100.0, nullable=False)
    recoverable_mass_kg = Column(Float, nullable=True)
    waste_loss_kg = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to detected individual objects in this session
    detected_objects = relationship(
        "DetectedObject",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Relationship to stream-wise analysis records in this session
    stream_analyses = relationship(
        "StreamAnalysis",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
