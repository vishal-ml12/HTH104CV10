from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    service: str


class MaterialItem(BaseModel):
    name: str
    confidence: float


class ContaminationItem(BaseModel):
    level: str
    percentage: float


class BoundingBoxCoordinates(BaseModel):
    x: float
    y: float
    width: float
    height: float
    normalized: Optional[Dict[str, float]] = None


class DetectedObjectSchema(BaseModel):
    object_id: str
    material: str
    confidence: float
    confidence_level: Optional[str] = "high"
    stream: str
    status: str
    contamination_category: Optional[str] = "none"
    contamination_severity: Optional[str] = "low"
    contamination_score: Optional[float] = 0.0
    bbox: Optional[Dict[str, Any]] = None


class StreamDetail(BaseModel):
    name: str
    color: str
    count: int
    percentage: float
    diverter_bin: str
    items: List[DetectedObjectSchema] = []


class VirtualSortingResult(BaseModel):
    total_objects: int
    dominant_stream: str
    streams: Dict[str, StreamDetail]
    diverter_events: List[str] = []
    simulation_notice: str


class StreamAnalysisSchema(BaseModel):
    stream_name: str
    item_count: int
    stream_share_pct: float
    contamination_category: str
    contamination_level: str
    contamination_percentage: float
    quality_score: float
    estimated_yield: float
    yield_loss_handling: float
    yield_loss_contamination: float
    recoverable_mass_kg: float
    waste_loss_kg: float
    processing_route: str
    recommendation: str
    recommendation_reason: str


class YieldLossBreakdown(BaseModel):
    baseline_potential: float
    mechanical_handling_loss: float
    contamination_rejection_loss: float
    net_estimated_yield: float


class ExplainabilitySchema(BaseModel):
    recommendation: str
    reason: str
    technical_justification: str


class OptimizationDetail(BaseModel):
    primary_material: str
    confidence: float
    total_objects: int
    input_mass_kg: float
    recoverable_mass_kg: float
    waste_loss_kg: float
    contamination_percentage: float
    quality_score: float
    recycling_yield: float
    yield_loss_breakdown: YieldLossBreakdown
    processing_route: str
    recommendation: str
    recommendation_reason: str
    explainability: ExplainabilitySchema


class AnalysisDetail(BaseModel):
    materials: List[MaterialItem]
    contamination: ContaminationItem
    quality_score: float
    recycling_yield: float
    recommendation: str
    recommendation_reason: Optional[str] = None
    processing_route: Optional[str] = None
    detected_objects: List[DetectedObjectSchema] = []
    virtual_sorting: Optional[VirtualSortingResult] = None
    streams_analysis: Optional[Dict[str, StreamAnalysisSchema]] = None
    optimization: Optional[OptimizationDetail] = None
    image_dimensions: Optional[Dict[str, int]] = None


class AnalysisResponse(BaseModel):
    success: bool
    session_id: str
    mode: str
    analysis: AnalysisDetail


class WasteAnalysisRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: Optional[str] = None
    material: str
    confidence: float
    contamination_level: str
    contamination_percentage: float
    quality_score: float
    recycling_yield: float
    recommendation: str
    recommendation_reason: Optional[str] = None
    processing_route: Optional[str] = None
    input_mass_kg: float = 100.0
    recoverable_mass_kg: Optional[float] = None
    waste_loss_kg: Optional[float] = None
    total_objects: int = 1
    plastic_count: int = 0
    glass_count: int = 0
    metal_count: int = 0
    paper_count: int = 0
    organic_count: int = 0
    review_count: int = 0
    mode: str = "REAL_YOLO"
    image_name: Optional[str] = None
    created_at: datetime


class DetectedObjectRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    session_id: str
    object_id: str
    material: str
    confidence: float
    box_x: float
    box_y: float
    box_width: float
    box_height: float
    stream: str
    status: str
    reviewed_material: Optional[str] = None
    contamination_score: float = 0.0
    contamination_category: str = "none"
    created_at: datetime


class StreamAnalysisRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    session_id: str
    stream_name: str
    item_count: int
    stream_share_pct: float
    contamination_category: str
    contamination_level: str
    contamination_percentage: float
    quality_score: float
    estimated_yield: float
    yield_loss_handling: float
    yield_loss_contamination: float
    recoverable_mass_kg: float
    waste_loss_kg: float
    processing_route: str
    recommendation: str
    recommendation_reason: str
    created_at: datetime


class StatisticsResponse(BaseModel):
    total_analyses: int
    total_objects_detected: int = 0
    plastic_objects: int = 0
    glass_objects: int = 0
    metal_objects: int = 0
    paper_objects: int = 0
    organic_objects: int = 0
    review_queue_objects: int = 0
    average_contamination: float
    average_quality_score: float
    average_recycling_yield: float
    total_recoverable_kg: float = 0.0
    total_waste_loss_kg: float = 0.0


class ReclassifyRequest(BaseModel):
    new_material: str
    notes: Optional[str] = None


class BatchAnalyzeResponse(BaseModel):
    success: bool
    batch_size: int
    sessions: List[Dict[str, Any]]
    batch_summary: Dict[str, Any]


class ConveyorControlRequest(BaseModel):
    action: str  # start | pause | reset | set_speed
    speed: Optional[float] = 1.0


class ConveyorStepRequest(BaseModel):
    delta_time: Optional[float] = 1.0

