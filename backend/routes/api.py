import os
import uuid
from typing import List, Optional, Dict, Any
from collections import Counter
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

import tempfile
from backend.database.session import get_db
from backend.models.waste_analysis import WasteAnalysis
from backend.models.detected_object import DetectedObject
from backend.models.stream_analysis import StreamAnalysis
from backend.schemas.analysis import (
    HealthResponse,
    AnalysisResponse,
    WasteAnalysisRecord,
    DetectedObjectRecord,
    StreamAnalysisRecord,
    StatisticsResponse,
    ReclassifyRequest,
    BatchAnalyzeResponse,
    ConveyorControlRequest,
    ConveyorStepRequest,
)
from backend.services.ai_service import get_ai_service, BaseAIService
from backend.services.yield_service import get_yield_service, YieldService
from backend.services.sorting_service import get_sorting_engine, VirtualSortingEngine, MATERIAL_TO_STREAM
from backend.services.video_service import video_conveyor_service
from backend.services.conveyor_simulation import conveyor_simulation

router = APIRouter(prefix="/api", tags=["Waste Recycling & Virtual Sorting"])

MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".avi", ".mov", ".mkv"}



def add_no_cache_headers(response: Response):
    """Ensure responses are never cached by intermediate proxies or browsers."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"


@router.get("/health", response_model=HealthResponse)
def health_check(response: Response):
    """Health check endpoint to verify backend service status."""
    add_no_cache_headers(response)
    return {
        "status": "ok",
        "service": "Waste Recycling Optimizer"
    }


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_waste(
    response: Response,
    file: Optional[UploadFile] = File(None),
    input_mass_kg: float = Form(100.0),
    db: Session = Depends(get_db),
    ai_srv: BaseAIService = Depends(get_ai_service),
    yield_srv: YieldService = Depends(get_yield_service),
    sorting_srv: VirtualSortingEngine = Depends(get_sorting_engine),
):
    """
    Phase 2 Core Pipeline:
    1. Multi-object computer vision detection (YOLO11n ONNX) & crop contamination assessment.
    2. Virtual sorting engine (6 material streams).
    3. Stream-wise contamination analysis, quality scoring, yield-loss breakdown, and mass balance.
    4. Operational recommendation engine with explainability (Recommendation + Reason).
    5. Full persistence in MySQL (waste_analysis, detected_objects, stream_analyses).
    """
    add_no_cache_headers(response)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select a valid image file."
        )

    filename = file.filename or ""
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_IMAGE_EXTENSIONS and file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Please upload an image (JPG, PNG, WEBP)."
        )

    try:
        image_bytes = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded image. Please try again."
        )

    if not image_bytes or len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty. Please select a valid file."
        )

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file exceeds the maximum size limit of 15MB."
        )

    # Generate unique analysis session ID
    session_id = f"sess_{uuid.uuid4().hex[:12]}"

    try:
        # Step 1: AI Multi-Object Detection & Crop-Level Contamination
        detection_raw = ai_srv.detect_waste_and_contamination(
            image_bytes=image_bytes,
            filename=filename
        )
    except RuntimeError as re:
        if "AI model is not available" in str(re):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI model is not available. Please check model configuration."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI inference engine failed. Please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing image: {str(e)}"
        )

    try:
        mode = detection_raw.get("mode", "REAL_YOLO")
        raw_detected_objects = detection_raw.get("detected_objects", [])

        # Step 2: Virtual Sorting Engine (routing objects to 6 streams)
        sorting_result = sorting_srv.sort_stream(raw_detected_objects)

        # Step 3: Phase 2 Stream-Wise Contamination Analysis, Quality, Yield, and Optimization
        overall_contam_pct = float(detection_raw.get("contamination_percentage", 18.0))
        contamination_level = str(detection_raw.get("contamination_level", "medium")).lower()

        materials = detection_raw.get("materials", [])
        primary_material = detection_raw.get("primary_material") or (materials[0]["name"] if materials else "unknown")
        confidence = float(detection_raw.get("primary_confidence") or (materials[0]["confidence"] if materials else 0.0))

        optimization_data = yield_srv.optimize_batch(
            detected_objects=raw_detected_objects,
            virtual_sorting_streams=sorting_result["streams"],
            primary_material=primary_material,
            primary_confidence=confidence,
            overall_contamination_pct=overall_contam_pct,
            input_mass_kg=input_mass_kg,
        )

        overall_opt = optimization_data["overall_optimization"]
        streams_analysis = optimization_data["streams_analysis"]

        quality_score = float(overall_opt["quality_score"])
        recycling_yield = float(overall_opt["recycling_yield"])
        recommendation = overall_opt["recommendation"]
        recommendation_reason = overall_opt["recommendation_reason"]
        processing_route = overall_opt["processing_route"]
        recoverable_mass_kg = float(overall_opt["recoverable_mass_kg"])
        waste_loss_kg = float(overall_opt["waste_loss_kg"])

        # Stream counts
        streams_data = sorting_result["streams"]
        plastic_cnt = streams_data.get("plastic", {}).get("count", 0)
        glass_cnt = streams_data.get("glass", {}).get("count", 0)
        metal_cnt = streams_data.get("metal", {}).get("count", 0)
        paper_cnt = streams_data.get("paper", {}).get("count", 0)
        organic_cnt = streams_data.get("organic", {}).get("count", 0)
        review_cnt = streams_data.get("review", {}).get("count", 0)
        total_objects = sorting_result.get("total_objects", len(raw_detected_objects))

        # Step 4: Persist Session Record into MySQL
        db_session = WasteAnalysis(
            session_id=session_id,
            material=primary_material,
            confidence=confidence,
            contamination_level=contamination_level,
            contamination_percentage=overall_contam_pct,
            quality_score=quality_score,
            recycling_yield=recycling_yield,
            recommendation=recommendation,
            recommendation_reason=recommendation_reason,
            processing_route=processing_route,
            input_mass_kg=input_mass_kg,
            recoverable_mass_kg=recoverable_mass_kg,
            waste_loss_kg=waste_loss_kg,
            total_objects=total_objects,
            plastic_count=plastic_cnt,
            glass_count=glass_cnt,
            metal_count=metal_cnt,
            paper_count=paper_cnt,
            organic_count=organic_cnt,
            review_count=review_cnt,
            mode=mode,
            image_name=filename,
        )
        db.add(db_session)
        db.flush()  # Generates db_session.id

        # Step 5: Persist Individual Detected Objects into MySQL
        for obj in raw_detected_objects:
            bbox = obj.get("bbox", {})
            db_obj = DetectedObject(
                analysis_id=db_session.id,
                session_id=session_id,
                object_id=obj.get("object_id", "obj_1"),
                material=obj.get("material", "unknown"),
                confidence=float(obj.get("confidence", 0.0)),
                box_x=float(bbox.get("x", 0.0)),
                box_y=float(bbox.get("y", 0.0)),
                box_width=float(bbox.get("width", 0.0)),
                box_height=float(bbox.get("height", 0.0)),
                stream=obj.get("stream", "review"),
                status=obj.get("status", "sorted"),
                contamination_score=float(obj.get("contamination_score", 0.0)),
                contamination_category=str(obj.get("contamination_category", "none")),
            )
            db.add(db_obj)

        # Step 6: Persist Stream-Wise Analysis Records into MySQL
        for s_name, s_data in streams_analysis.items():
            db_stream = StreamAnalysis(
                analysis_id=db_session.id,
                session_id=session_id,
                stream_name=s_name,
                item_count=s_data["item_count"],
                stream_share_pct=s_data["stream_share_pct"],
                contamination_category=s_data["contamination_category"],
                contamination_level=s_data["contamination_level"],
                contamination_percentage=s_data["contamination_percentage"],
                quality_score=s_data["quality_score"],
                estimated_yield=s_data["estimated_yield"],
                yield_loss_handling=s_data["yield_loss_handling"],
                yield_loss_contamination=s_data["yield_loss_contamination"],
                recoverable_mass_kg=s_data["recoverable_mass_kg"],
                waste_loss_kg=s_data["waste_loss_kg"],
                processing_route=s_data["processing_route"],
                recommendation=s_data["recommendation"],
                recommendation_reason=s_data["recommendation_reason"],
            )
            db.add(db_stream)

        db.commit()
        db.refresh(db_session)

        # Assemble full response
        return {
            "success": True,
            "session_id": session_id,
            "mode": mode,
            "analysis": {
                "materials": materials if materials else [{"name": primary_material, "confidence": confidence}],
                "contamination": {
                    "level": contamination_level,
                    "percentage": overall_contam_pct,
                },
                "quality_score": quality_score,
                "recycling_yield": recycling_yield,
                "recommendation": recommendation,
                "recommendation_reason": recommendation_reason,
                "processing_route": processing_route,
                "detected_objects": raw_detected_objects,
                "virtual_sorting": sorting_result,
                "streams_analysis": streams_analysis,
                "optimization": overall_opt,
                "image_dimensions": detection_raw.get("image_dimensions", {"width": 640, "height": 640}),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis processing or database persistence failed: {str(e)}"
        )


@router.post("/batch-analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze_waste(
    response: Response,
    files: List[UploadFile] = File(...),
    input_mass_kg: float = Form(100.0),
    db: Session = Depends(get_db),
    ai_srv: BaseAIService = Depends(get_ai_service),
    yield_srv: YieldService = Depends(get_yield_service),
    sorting_srv: VirtualSortingEngine = Depends(get_sorting_engine),
):
    """
    Phase 2 Batch Analysis Endpoint:
    Analyzes multiple waste stream images concurrently, aggregates stream distributions,
    and returns comprehensive batch yield optimization metrics.
    """
    add_no_cache_headers(response)

    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided for batch processing.")

    batch_sessions = []
    total_objects_all = 0
    total_recoverable_kg = 0.0
    total_waste_loss_kg = 0.0
    material_dist = Counter()
    stream_dist = Counter()
    all_quality_scores = []
    all_yield_scores = []

    per_file_mass = input_mass_kg / len(files)

    for f in files:
        try:
            content = await f.read()
            if not content:
                continue

            sess_id = f"batch_{uuid.uuid4().hex[:10]}"
            detection = ai_srv.detect_waste_and_contamination(content, f.filename or "batch_item")
            sorting = sorting_srv.sort_stream(detection.get("detected_objects", []))

            opt = yield_srv.optimize_batch(
                detected_objects=detection.get("detected_objects", []),
                virtual_sorting_streams=sorting["streams"],
                primary_material=detection.get("primary_material", "unknown"),
                primary_confidence=detection.get("primary_confidence", 0.8),
                overall_contamination_pct=detection.get("contamination_percentage", 18.0),
                input_mass_kg=per_file_mass,
            )

            overall = opt["overall_optimization"]
            total_objects_all += overall["total_objects"]
            total_recoverable_kg += overall["recoverable_mass_kg"]
            total_waste_loss_kg += overall["waste_loss_kg"]
            all_quality_scores.append(overall["quality_score"])
            all_yield_scores.append(overall["recycling_yield"])
            material_dist[overall["primary_material"]] += 1

            for s_name, s_info in sorting["streams"].items():
                stream_dist[s_name] += s_info["count"]

            batch_sessions.append({
                "filename": f.filename,
                "session_id": sess_id,
                "primary_material": overall["primary_material"],
                "total_objects": overall["total_objects"],
                "quality_score": overall["quality_score"],
                "recycling_yield": overall["recycling_yield"],
                "recoverable_mass_kg": overall["recoverable_mass_kg"],
                "waste_loss_kg": overall["waste_loss_kg"],
                "processing_route": overall["processing_route"],
                "recommendation": overall["recommendation"],
            })
        except Exception as e:
            print(f"Error in batch item {f.filename}: {e}")

    avg_quality = round(sum(all_quality_scores) / len(all_quality_scores), 1) if all_quality_scores else 0.0
    avg_yield = round(sum(all_yield_scores) / len(all_yield_scores), 1) if all_yield_scores else 0.0

    return {
        "success": True,
        "batch_size": len(files),
        "sessions": batch_sessions,
        "batch_summary": {
            "total_objects_detected": total_objects_all,
            "total_input_mass_kg": input_mass_kg,
            "total_recoverable_kg": round(total_recoverable_kg, 2),
            "total_waste_loss_kg": round(total_waste_loss_kg, 2),
            "average_quality_score": avg_quality,
            "average_recycling_yield": avg_yield,
            "material_distribution": dict(material_dist),
            "stream_distribution": dict(stream_dist),
        }
    }


@router.get("/results", response_model=List[WasteAnalysisRecord])
def get_results(
    response: Response,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Fetch previously stored analysis sessions from MySQL."""
    add_no_cache_headers(response)
    try:
        records = (
            db.query(WasteAnalysis)
            .order_by(WasteAnalysis.id.desc())
            .limit(limit)
            .all()
        )
        return records
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load analysis history from database."
        )


@router.get("/sessions/{session_id}")
def get_session_details(
    session_id: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """Fetch complete analysis session along with detected objects and stream-wise analyses."""
    add_no_cache_headers(response)
    session_rec = db.query(WasteAnalysis).filter(WasteAnalysis.session_id == session_id).first()
    if not session_rec:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    objects = db.query(DetectedObject).filter(DetectedObject.session_id == session_id).all()
    streams = db.query(StreamAnalysis).filter(StreamAnalysis.session_id == session_id).all()

    return {
        "session": session_rec,
        "detected_objects": objects,
        "stream_analyses": streams,
    }


@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics(
    response: Response,
    db: Session = Depends(get_db)
):
    """Calculate and return aggregate statistics across stored analyses, virtual streams, and mass balance."""
    add_no_cache_headers(response)
    try:
        total = db.query(func.count(WasteAnalysis.id)).scalar() or 0

        if total == 0:
            return {
                "total_analyses": 0,
                "total_objects_detected": 0,
                "plastic_objects": 0,
                "glass_objects": 0,
                "metal_objects": 0,
                "paper_objects": 0,
                "organic_objects": 0,
                "review_queue_objects": 0,
                "average_contamination": 0.0,
                "average_quality_score": 0.0,
                "average_recycling_yield": 0.0,
                "total_recoverable_kg": 0.0,
                "total_waste_loss_kg": 0.0,
            }

        total_objs = db.query(func.sum(WasteAnalysis.total_objects)).scalar() or 0
        plastic_objs = db.query(func.sum(WasteAnalysis.plastic_count)).scalar() or 0
        glass_objs = db.query(func.sum(WasteAnalysis.glass_count)).scalar() or 0
        metal_objs = db.query(func.sum(WasteAnalysis.metal_count)).scalar() or 0
        paper_objs = db.query(func.sum(WasteAnalysis.paper_count)).scalar() or 0
        organic_objs = db.query(func.sum(WasteAnalysis.organic_count)).scalar() or 0
        review_objs = db.query(func.sum(WasteAnalysis.review_count)).scalar() or 0

        avg_contam = db.query(func.avg(WasteAnalysis.contamination_percentage)).scalar() or 0.0
        avg_quality = db.query(func.avg(WasteAnalysis.quality_score)).scalar() or 0.0
        avg_yield = db.query(func.avg(WasteAnalysis.recycling_yield)).scalar() or 0.0
        tot_recoverable = db.query(func.sum(WasteAnalysis.recoverable_mass_kg)).scalar() or 0.0
        tot_waste_loss = db.query(func.sum(WasteAnalysis.waste_loss_kg)).scalar() or 0.0

        return {
            "total_analyses": total,
            "total_objects_detected": int(total_objs),
            "plastic_objects": int(plastic_objs),
            "glass_objects": int(glass_objs),
            "metal_objects": int(metal_objs),
            "paper_objects": int(paper_objs),
            "organic_objects": int(organic_objs),
            "review_queue_objects": int(review_objs),
            "average_contamination": round(float(avg_contam), 2),
            "average_quality_score": round(float(avg_quality), 2),
            "average_recycling_yield": round(float(avg_yield), 2),
            "total_recoverable_kg": round(float(tot_recoverable), 2),
            "total_waste_loss_kg": round(float(tot_waste_loss), 2),
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to compute database statistics."
        )


@router.get("/analytics/trends")
def get_analytics_trends(
    response: Response,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """
    Phase 2 Historical Analytics:
    Returns chronological contamination trends, quality trends, yield trends, and mass balance series.
    """
    add_no_cache_headers(response)
    try:
        records = (
            db.query(WasteAnalysis)
            .order_by(WasteAnalysis.id.desc())
            .limit(limit)
            .all()
        )
        records.reverse()  # Chronological order

        timestamps = [r.created_at.strftime("%H:%M:%S") for r in records]
        session_ids = [r.session_id or f"id_{r.id}" for r in records]
        contam_series = [r.contamination_percentage for r in records]
        quality_series = [r.quality_score for r in records]
        yield_series = [r.recycling_yield for r in records]
        recoverable_series = [round(r.recoverable_mass_kg or (r.recycling_yield * 1.0), 1) for r in records]

        return {
            "timestamps": timestamps,
            "session_ids": session_ids,
            "contamination_trend": contam_series,
            "quality_trend": quality_series,
            "yield_trend": yield_series,
            "recoverable_mass_trend": recoverable_series,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch analytics trends: {str(e)}"
        )


@router.get("/analytics/streams")
def get_stream_analytics(
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Phase 2 Stream Comparison Analytics:
    Computes comparative metrics across all 6 material streams (Plastic, Glass, Metal, Paper, Organic, Review).
    """
    add_no_cache_headers(response)
    try:
        stream_keys = ["plastic", "glass", "metal", "paper", "organic", "review"]
        result = {}

        for s_name in stream_keys:
            stats = (
                db.query(
                    func.count(StreamAnalysis.id).label("total_batches"),
                    func.sum(StreamAnalysis.item_count).label("total_items"),
                    func.avg(StreamAnalysis.contamination_percentage).label("avg_contam"),
                    func.avg(StreamAnalysis.quality_score).label("avg_quality"),
                    func.avg(StreamAnalysis.estimated_yield).label("avg_yield"),
                    func.sum(StreamAnalysis.recoverable_mass_kg).label("total_recoverable_kg"),
                    func.sum(StreamAnalysis.waste_loss_kg).label("total_waste_loss_kg"),
                )
                .filter(StreamAnalysis.stream_name == s_name)
                .first()
            )

            # Get dominant contamination category
            top_cat_row = (
                db.query(StreamAnalysis.contamination_category, func.count(StreamAnalysis.id))
                .filter(StreamAnalysis.stream_name == s_name, StreamAnalysis.contamination_category != "none")
                .group_by(StreamAnalysis.contamination_category)
                .order_by(func.count(StreamAnalysis.id).desc())
                .first()
            )
            top_cat = top_cat_row[0] if top_cat_row else "none"

            result[s_name] = {
                "stream_name": s_name,
                "total_items": int(stats.total_items or 0) if stats else 0,
                "avg_contamination": round(float(stats.avg_contam or 0.0), 1) if stats else 0.0,
                "avg_quality": round(float(stats.avg_quality or 0.0), 1) if stats else 0.0,
                "avg_yield": round(float(stats.avg_yield or 0.0), 1) if stats else 0.0,
                "total_recoverable_kg": round(float(stats.total_recoverable_kg or 0.0), 1) if stats else 0.0,
                "total_waste_loss_kg": round(float(stats.total_waste_loss_kg or 0.0), 1) if stats else 0.0,
                "dominant_contamination_category": top_cat,
            }

        return {"streams": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stream analytics: {str(e)}"
        )


@router.get("/review-queue", response_model=List[DetectedObjectRecord])
def get_review_queue(
    response: Response,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Fetch items currently in the Human Review Queue (pending verification or flagged)."""
    add_no_cache_headers(response)
    try:
        items = (
            db.query(DetectedObject)
            .filter(DetectedObject.status.in_(["pending_review", "needs_review"]))
            .order_by(DetectedObject.id.desc())
            .limit(limit)
            .all()
        )
        return items
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch human review queue."
        )


@router.post("/review-queue/{object_db_id}/reclassify")
def reclassify_review_item(
    object_db_id: int,
    request: ReclassifyRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Human Reviewer action: verify or reclassify a flagged object into a designated stream."""
    add_no_cache_headers(response)
    obj = db.query(DetectedObject).filter(DetectedObject.id == object_db_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Review object not found.")

    new_mat = request.new_material.lower().strip()
    new_stream = MATERIAL_TO_STREAM.get(new_mat, "review")
    prev_stream = obj.stream

    obj.reviewed_material = new_mat
    obj.material = new_mat
    obj.stream = new_stream
    obj.status = "reclassified"

    # Synchronize parent session stream counters if linked
    if obj.analysis_id:
        parent = db.query(WasteAnalysis).filter(WasteAnalysis.id == obj.analysis_id).first()
        if parent:
            if prev_stream == "review" and parent.review_count > 0:
                parent.review_count -= 1
            if new_stream == "plastic":
                parent.plastic_count += 1
            elif new_stream == "glass":
                parent.glass_count += 1
            elif new_stream == "metal":
                parent.metal_count += 1
            elif new_stream == "paper":
                parent.paper_count += 1
            elif new_stream == "organic":
                parent.organic_count += 1

    db.commit()
    db.refresh(obj)
    return {
        "success": True,
        "message": f"Object {obj.object_id} successfully reclassified to '{new_mat}' ({new_stream} stream).",
        "object": obj
    }


# =====================================================================
# PHASE 3: VIDEO PROCESSING & CONVEYOR SIMULATION ENDPOINTS
# =====================================================================

@router.post("/video/analyze", status_code=status.HTTP_200_OK)
async def analyze_video_stream(
    response: Response,
    file: Optional[UploadFile] = File(None),
    input_mass_kg: float = Form(100.0),
    db: Session = Depends(get_db),
):
    """
    Phase 3 Video Stream Pipeline:
    1. Ingests video upload (.mp4, .webm, .avi, .mov).
    2. Adaptive frame sampling (1-2 FPS keyframe sampling).
    3. Multi-object computer vision detection (YOLO11n ONNX) on sampled frames.
    4. Centroid & IoU association tracking with persistent track IDs.
    5. Virtual conveyor belt diverter simulation into 6 lanes with timestamped event logging.
    6. Stream-wise optimization (yield, purity, mass balance) on unique tracked objects.
    7. Full persistence in MySQL (waste_analysis, detected_objects, stream_analyses).
    """
    add_no_cache_headers(response)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select a valid video file."
        )

    filename = file.filename or ""
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_VIDEO_EXTENSIONS and file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '{ext}'. Please upload MP4, WEBM, AVI, or MOV."
        )

    # Save to temp file for OpenCV VideoCapture
    temp_video_fd, temp_video_path = tempfile.mkstemp(suffix=ext if ext else ".mp4")
    try:
        total_bytes = 0
        with os.fdopen(temp_video_fd, "wb") as f_out:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_VIDEO_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Uploaded video exceeds the maximum size limit of 50MB."
                    )
                f_out.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded video file is empty."
            )

        # Run Video Conveyor Analysis
        result = video_conveyor_service.analyze_video(
            video_path=temp_video_path,
            input_mass_kg=input_mass_kg,
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process video: {str(e)}"
        )
    finally:
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except OSError:
                pass

    session_id = f"vid_{uuid.uuid4().hex[:12]}"
    opt = result["optimization"]

    contam_pct = float(opt.get("contamination_percentage", 15.0))
    if contam_pct < 15.0:
        contam_lvl = "low"
    elif contam_pct <= 35.0:
        contam_lvl = "medium"
    else:
        contam_lvl = "high"

    # Persist in MySQL
    db_analysis = WasteAnalysis(
        session_id=session_id,
        material=result.get("primary_material", "plastic"),
        confidence=float(result.get("confidence", 0.90)),
        contamination_level=contam_lvl,
        contamination_percentage=contam_pct,
        quality_score=float(opt.get("quality_score", 85.0)),
        recycling_yield=float(opt.get("recycling_yield", 82.0)),
        recommendation=str(opt.get("recommendation", "Direct mechanical reprocessing")),
        recommendation_reason=str(opt.get("recommendation_reason", "")),
        processing_route=str(opt.get("processing_route", "DIRECT_RECYCLING")),
        input_mass_kg=float(input_mass_kg),
        recoverable_mass_kg=float(opt.get("recoverable_mass_kg", 82.0)),
        waste_loss_kg=float(opt.get("waste_loss_kg", 18.0)),
        total_objects=int(result.get("unique_objects_count", 1)),
        plastic_count=int(result["virtual_sorting"]["streams"].get("plastic", {}).get("count", 0)),
        glass_count=int(result["virtual_sorting"]["streams"].get("glass", {}).get("count", 0)),
        metal_count=int(result["virtual_sorting"]["streams"].get("metal", {}).get("count", 0)),
        paper_count=int(result["virtual_sorting"]["streams"].get("paper", {}).get("count", 0)),
        organic_count=int(result["virtual_sorting"]["streams"].get("organic", {}).get("count", 0)),
        review_count=int(result["virtual_sorting"]["streams"].get("review", {}).get("count", 0)),
        mode=str(result.get("mode", "REAL_YOLO")),
        image_name=filename,
    )
    db.add(db_analysis)
    db.flush()

    # Save DetectedObject records for unique tracked objects
    for obj in result.get("unique_tracked_objects", []):
        bbox = obj.get("bbox", {})
        db_obj = DetectedObject(
            analysis_id=db_analysis.id,
            session_id=session_id,
            object_id=str(obj.get("object_id", "track_1")),
            material=str(obj.get("material", "plastic")),
            confidence=float(obj.get("confidence", 0.9)),
            box_x=float(bbox.get("x", 0.0)),
            box_y=float(bbox.get("y", 0.0)),
            box_width=float(bbox.get("width", 0.0)),
            box_height=float(bbox.get("height", 0.0)),
            stream=str(obj.get("stream", "plastic")),
            status=str(obj.get("status", "sorted")),
            contamination_score=float(obj.get("contamination_score", 0.0)),
            contamination_category=str(obj.get("contamination_category", "none")),
        )
        db.add(db_obj)

    # Save StreamAnalysis records
    for st_key, st_info in result.get("streams_analysis", {}).items():
        db_stream = StreamAnalysis(
            analysis_id=db_analysis.id,
            session_id=session_id,
            stream_name=st_key,
            item_count=int(st_info.get("item_count", 0)),
            stream_share_pct=float(st_info.get("stream_share_pct", 0.0)),
            contamination_category=str(st_info.get("contamination_category", "none")),
            contamination_level=str(st_info.get("contamination_level", "low")),
            contamination_percentage=float(st_info.get("contamination_percentage", 0.0)),
            quality_score=float(st_info.get("quality_score", 0.0)),
            estimated_yield=float(st_info.get("estimated_yield", 0.0)),
            yield_loss_handling=float(st_info.get("yield_loss_handling", 0.0)),
            yield_loss_contamination=float(st_info.get("yield_loss_contamination", 0.0)),
            recoverable_mass_kg=float(st_info.get("recoverable_mass_kg", 0.0)),
            waste_loss_kg=float(st_info.get("waste_loss_kg", 0.0)),
            processing_route=str(st_info.get("processing_route", "DIRECT_RECYCLING")),
            recommendation=str(st_info.get("recommendation", "Direct reprocessing")),
            recommendation_reason=str(st_info.get("recommendation_reason", "")),
        )
        db.add(db_stream)

    db.commit()

    return {
        "success": True,
        "session_id": session_id,
        "mode": result["mode"],
        "video_metadata": result["video_metadata"],
        "total_frames_sampled": result["total_frames_sampled"],
        "unique_objects_count": result["unique_objects_count"],
        "conveyor_timeline": result["conveyor_timeline"],
        "virtual_sorting": result["virtual_sorting"],
        "streams_analysis": result["streams_analysis"],
        "optimization": result["optimization"],
        "primary_material": result["primary_material"],
        "confidence": result["confidence"],
        "event_logs": result["event_logs"],
        "disclaimer": "Software-based conveyor diversion simulation. No physical machinery connected.",
    }


@router.get("/conveyor/telemetry")
def get_conveyor_telemetry(response: Response):
    """Fetch live telemetry snapshot of the virtual conveyor belt simulation."""
    add_no_cache_headers(response)
    return conveyor_simulation.get_snapshot()


@router.post("/conveyor/step")
def step_conveyor(
    response: Response,
    request: Optional[ConveyorStepRequest] = None
):
    """Advance the virtual conveyor belt simulation by one time step."""
    add_no_cache_headers(response)
    dt = request.delta_time if request and request.delta_time is not None else 1.0
    return conveyor_simulation.step(delta_time=dt)


@router.post("/conveyor/control")
def control_conveyor(
    request: ConveyorControlRequest,
    response: Response
):
    """
    Control virtual conveyor belt simulation:
    - action: "start" | "pause" | "reset" | "set_speed"
    - speed: float multiplier (e.g. 0.5, 1.0, 2.0)
    """
    add_no_cache_headers(response)
    action = request.action.lower().strip()
    if action == "start":
        return conveyor_simulation.start()
    elif action == "pause":
        return conveyor_simulation.pause()
    elif action == "reset":
        return conveyor_simulation.reset()
    elif action == "set_speed":
        speed = request.speed if request.speed is not None else 1.0
        return conveyor_simulation.set_speed(speed)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown control action '{action}'. Supported actions: start, pause, reset, set_speed."
        )

