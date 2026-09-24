from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.session import Base


class StreamAnalysis(Base):
    """
    Relational model storing Phase 2 Stream-Wise Contamination, Quality,
    and Yield Optimization records for every separated material stream.
    """
    __tablename__ = "stream_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("waste_analysis.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)

    stream_name = Column(String(50), nullable=False, index=True)  # plastic, glass, metal, paper, organic, review
    item_count = Column(Integer, default=0, nullable=False)
    stream_share_pct = Column(Float, default=0.0, nullable=False)

    contamination_category = Column(String(64), default="none", nullable=False)
    contamination_level = Column(String(30), default="low", nullable=False)
    contamination_percentage = Column(Float, default=0.0, nullable=False)

    quality_score = Column(Float, default=0.0, nullable=False)
    estimated_yield = Column(Float, default=0.0, nullable=False)
    yield_loss_handling = Column(Float, default=0.0, nullable=False)
    yield_loss_contamination = Column(Float, default=0.0, nullable=False)

    recoverable_mass_kg = Column(Float, default=0.0, nullable=False)
    waste_loss_kg = Column(Float, default=0.0, nullable=False)

    processing_route = Column(String(64), default="DIRECT_RECYCLING", nullable=False)
    recommendation = Column(String(255), nullable=False)
    recommendation_reason = Column(String(500), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    analysis = relationship("WasteAnalysis", back_populates="stream_analyses")
