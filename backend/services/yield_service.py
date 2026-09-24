"""
Phase 2 Yield Optimization, Stream-Wise Contamination Analysis,
and Explainable Recommendation Engine.

Analyzes every separated material stream (Plastic, Glass, Metal, Paper, Organic, Review):
1. Stream-wise contamination analysis and visual categorization.
2. Contamination severity rating (low, medium, high, critical).
3. Estimated quality/purity score (prototype index).
4. Estimated recycling yield & transparent yield-loss breakdown.
5. Recoverable material estimation based on input mass (kg).
6. Smart processing route recommendation with explainability (Recommendation + Reason).

IMPORTANT DISCLAIMER:
RGB computer vision analyzes surface visual characteristics only. It does NOT claim
hidden chemical contaminants, composite barrier layers, or invisible adhesives can be
detected without NIR/spectroscopy. Quality scores and yield estimations are algorithmic
prototype metrics, not certified industrial recovery rates.
"""

from typing import Dict, Any, List, Optional
from collections import Counter


class YieldOptimizationEngine:
    # Baseline theoretical recovery potentials by material stream
    BASELINE_YIELDS: Dict[str, float] = {
        "metal": 95.0,
        "glass": 92.0,
        "plastic": 88.0,
        "paper": 82.0,
        "organic": 75.0,
        "review": 45.0,
        "unknown": 40.0,
    }

    # Handling / mechanical transfer loss factor (fixed shredding/dust/friction loss)
    MECHANICAL_HANDLING_LOSS: float = 3.5

    # Visually detectable contamination categories
    CONTAMINATION_CATEGORIES = {
        "organic_residue": "food/beverage residues and biofilm",
        "label_adhesive": "adhesive stickers, paper labels, or heat-shrink sleeves",
        "cross_polymer": "cross-polymer co-mingling (e.g. PP caps or PE rings on PET)",
        "soil_dust": "particulate dirt, dust, and abrasive grit",
        "none": "clean, unadulterated stream",
    }

    # Category penalty weights on purity
    CATEGORY_PENALTIES: Dict[str, float] = {
        "organic_residue": 5.0,
        "cross_polymer": 4.5,
        "label_adhesive": 3.0,
        "soil_dust": 3.5,
        "none": 0.0,
    }

    @classmethod
    def calculate_stream_metrics(
        cls,
        stream_name: str,
        stream_items: List[Dict[str, Any]],
        total_session_objects: int,
        input_mass_kg: float = 100.0,
        confidence: float = 0.85
    ) -> Dict[str, Any]:
        """
        Analyze an individual separated material stream.
        """
        item_count = len(stream_items)
        share_pct = round((item_count / total_session_objects * 100.0), 1) if total_session_objects > 0 else 0.0

        if item_count == 0:
            return {
                "stream_name": stream_name,
                "item_count": 0,
                "stream_share_pct": 0.0,
                "contamination_category": "none",
                "contamination_level": "low",
                "contamination_percentage": 0.0,
                "quality_score": 100.0,
                "estimated_yield": cls.BASELINE_YIELDS.get(stream_name, 80.0),
                "yield_loss_handling": 0.0,
                "yield_loss_contamination": 0.0,
                "recoverable_mass_kg": 0.0,
                "waste_loss_kg": 0.0,
                "processing_route": "IDLE",
                "recommendation": "No material in stream",
                "recommendation_reason": "No objects diverted to this stream in current batch.",
            }

        # 1. Contamination Analysis
        contam_scores = [float(it.get("contamination_score", 15.0)) for it in stream_items]
        avg_contam = round(sum(contam_scores) / len(contam_scores), 1)

        # Dominant contamination category
        cat_counts = Counter(it.get("contamination_category", "none") for it in stream_items)
        # Filter out 'none' if other categories exist
        non_none_cats = {k: v for k, v in cat_counts.items() if k != "none"}
        dominant_cat = max(non_none_cats, key=non_none_cats.get) if non_none_cats else "none"

        # Contamination severity level
        if avg_contam < 15.0:
            severity = "low"
        elif avg_contam < 35.0:
            severity = "medium"
        elif avg_contam < 60.0:
            severity = "high"
        else:
            severity = "critical"

        # 2. Quality / Purity Score Calculation (Prototype Purity Index 0 - 100)
        penalty = cls.CATEGORY_PENALTIES.get(dominant_cat, 0.0)
        raw_quality = 100.0 - (avg_contam * 1.15) - penalty
        quality_score = max(0.0, min(100.0, round(raw_quality, 1)))

        # 3. Estimated Recycling Yield & Yield-Loss Breakdown
        baseline = cls.BASELINE_YIELDS.get(stream_name, 80.0)
        handling_loss = cls.MECHANICAL_HANDLING_LOSS
        contam_loss = round(avg_contam * 0.95, 1)

        raw_yield = baseline - handling_loss - contam_loss
        estimated_yield = max(0.0, min(98.0, round(raw_yield, 1)))

        # 4. Recoverable Material Estimation (Mass Balance)
        stream_mass = (share_pct / 100.0) * input_mass_kg
        recoverable_mass = round(stream_mass * (estimated_yield / 100.0), 2)
        waste_loss_mass = round(stream_mass - recoverable_mass, 2)

        # 5. Smart Processing Route & Explainable Recommendation
        route, rec_text, reason_text = cls.determine_route_and_explanation(
            material=stream_name,
            confidence=confidence,
            contamination_pct=avg_contam,
            quality_score=quality_score,
            estimated_yield=estimated_yield,
            dominant_cat=dominant_cat
        )

        return {
            "stream_name": stream_name,
            "item_count": item_count,
            "stream_share_pct": share_pct,
            "contamination_category": dominant_cat,
            "contamination_level": severity,
            "contamination_percentage": avg_contam,
            "quality_score": quality_score,
            "estimated_yield": estimated_yield,
            "yield_loss_handling": handling_loss,
            "yield_loss_contamination": contam_loss,
            "recoverable_mass_kg": recoverable_mass,
            "waste_loss_kg": waste_loss_mass,
            "processing_route": route,
            "recommendation": rec_text,
            "recommendation_reason": reason_text,
        }

    @classmethod
    def determine_route_and_explanation(
        cls,
        material: str,
        confidence: float,
        contamination_pct: float,
        quality_score: float,
        estimated_yield: float,
        dominant_cat: str
    ) -> (str, str, str):
        """
        Transparent, rule-based recommendation engine with explainability.
        Rules based on: Material, Confidence, Contamination %, Quality Score, Yield %.
        """
        cat_desc = cls.CONTAMINATION_CATEGORIES.get(dominant_cat, dominant_cat)

        # Rule 1: Low Confidence or Review Queue -> Manual Inspection
        if confidence < 0.50 or material in ["review", "unknown", "mixed_waste"]:
            route = "MANUAL_REVIEW_FLAGGED"
            rec = "Manual inspection conveyor diversion"
            reason = (
                f"Low confidence ({int(confidence*100)}%) or stream ambiguity detected. "
                f"Contamination = {contamination_pct}%, Quality = {quality_score}, Estimated Yield = {estimated_yield}%."
            )
            return route, rec, reason

        # Rule 2: Low Contamination + High Quality -> Direct Recycling
        if contamination_pct < 15.0 and quality_score >= 80.0 and confidence >= 0.70:
            route = "DIRECT_RECYCLING"
            rec = "Direct mechanical reprocessing"
            reason = (
                f"Direct recycling route recommended because Contamination = {contamination_pct}%, "
                f"Quality = {quality_score}/100, Estimated Yield = {estimated_yield}%. "
                f"Material visual purity meets melt-grade granulating standards."
            )
            return route, rec, reason

        # Rule 3: Medium Contamination -> Pre-Processing
        if contamination_pct <= 35.0:
            route = "PRE_PROCESSING_WASHING"
            rec = "Pre-processing recommended"
            reason = (
                f"Pre-processing recommended because Contamination = {contamination_pct}%, "
                f"Quality = {quality_score}/100, Estimated Yield = {estimated_yield}%. "
                f"Identified {cat_desc}; automated hot caustic wash and optical de-labeling will recover high-grade yield."
            )
            return route, rec, reason

        # Rule 4: High Contamination -> Secondary Processing / Shredding
        if contamination_pct <= 60.0:
            route = "SECONDARY_PROCESSING_SHREDDING"
            rec = "Secondary processing / shredding required"
            reason = (
                f"Secondary processing recommended because Contamination = {contamination_pct}%, "
                f"Quality = {quality_score}/100, Estimated Yield = {estimated_yield}%. "
                f"Heavy contamination requires mechanical liberation, density bath sink-float separation, and re-sorting."
            )
            return route, rec, reason

        # Rule 5: Critical Contamination / Very Low Quality -> Downgrade / RDF
        route = "DOWNGRADE_RDF"
        rec = "Downgrade to Refuse-Derived Fuel (RDF) or industrial filler"
        reason = (
            f"Downgrade recommended because Contamination = {contamination_pct}%, "
            f"Quality = {quality_score}/100, Estimated Yield = {estimated_yield}%. "
            f"Excessive contamination causes severe yield loss; direct polymer remelt is unviable."
        )
        return route, rec, reason

    @classmethod
    def optimize_batch(
        cls,
        detected_objects: List[Dict[str, Any]],
        virtual_sorting_streams: Dict[str, Any],
        primary_material: str,
        primary_confidence: float,
        overall_contamination_pct: float,
        input_mass_kg: float = 100.0
    ) -> Dict[str, Any]:
        """
        Orchestrates full Phase 2 optimization across all separated material streams
        plus aggregate session metrics.
        """
        total_objects = len(detected_objects)

        # Analyze each of the 6 virtual streams individually
        streams_analysis: Dict[str, Dict[str, Any]] = {}
        for stream_key in ["plastic", "glass", "metal", "paper", "organic", "review"]:
            stream_info = virtual_sorting_streams.get(stream_key, {})
            stream_items = stream_info.get("items", [])
            
            # If items not in virtual_sorting_streams, extract from detected_objects
            if not stream_items:
                stream_items = [obj for obj in detected_objects if obj.get("stream") == stream_key]

            streams_analysis[stream_key] = cls.calculate_stream_metrics(
                stream_name=stream_key,
                stream_items=stream_items,
                total_session_objects=total_objects,
                input_mass_kg=input_mass_kg,
                confidence=primary_confidence
            )

        # Calculate session-wide aggregate metrics
        active_streams = [s for s in streams_analysis.values() if s["item_count"] > 0]

        if active_streams:
            weighted_quality = sum(s["quality_score"] * s["stream_share_pct"] for s in active_streams) / 100.0
            weighted_yield = sum(s["estimated_yield"] * s["stream_share_pct"] for s in active_streams) / 100.0
            total_recoverable_kg = sum(s["recoverable_mass_kg"] for s in active_streams)
            total_waste_loss_kg = sum(s["waste_loss_kg"] for s in active_streams)
        else:
            weighted_quality = max(0.0, 100.0 - (overall_contamination_pct * 1.15))
            weighted_yield = max(0.0, cls.BASELINE_YIELDS.get(primary_material, 75.0) - overall_contamination_pct)
            total_recoverable_kg = round(input_mass_kg * (weighted_yield / 100.0), 2)
            total_waste_loss_kg = round(input_mass_kg - total_recoverable_kg, 2)

        weighted_quality = round(weighted_quality, 1)
        weighted_yield = round(weighted_yield, 1)

        # Determine overall primary route and explainable recommendation
        primary_route, primary_rec, primary_reason = cls.determine_route_and_explanation(
            material=primary_material,
            confidence=primary_confidence,
            contamination_pct=overall_contamination_pct,
            quality_score=weighted_quality,
            estimated_yield=weighted_yield,
            dominant_cat="mixed_waste" if total_objects > 1 else "none"
        )

        # Overall yield-loss breakdown
        overall_baseline = cls.BASELINE_YIELDS.get(primary_material, 85.0)
        overall_handling_loss = cls.MECHANICAL_HANDLING_LOSS
        overall_contam_loss = round(max(0.0, overall_baseline - overall_handling_loss - weighted_yield), 1)

        return {
            "streams_analysis": streams_analysis,
            "overall_optimization": {
                "primary_material": primary_material,
                "confidence": primary_confidence,
                "total_objects": total_objects,
                "input_mass_kg": input_mass_kg,
                "recoverable_mass_kg": round(total_recoverable_kg, 2),
                "waste_loss_kg": round(total_waste_loss_kg, 2),
                "contamination_percentage": overall_contamination_pct,
                "quality_score": weighted_quality,
                "recycling_yield": weighted_yield,
                "yield_loss_breakdown": {
                    "baseline_potential": overall_baseline,
                    "mechanical_handling_loss": overall_handling_loss,
                    "contamination_rejection_loss": overall_contam_loss,
                    "net_estimated_yield": weighted_yield,
                },
                "processing_route": primary_route,
                "recommendation": primary_rec,
                "recommendation_reason": primary_reason,
                "explainability": {
                    "recommendation": primary_rec,
                    "reason": f"Contamination = {overall_contamination_pct}%, Quality = {weighted_quality}/100, Estimated Yield = {weighted_yield}%",
                    "technical_justification": primary_reason,
                }
            }
        }


# Singleton service instance
yield_service = YieldOptimizationEngine()
YieldService = YieldOptimizationEngine


def get_yield_service() -> YieldOptimizationEngine:
    """FastAPI dependency for YieldOptimizationEngine."""
    return yield_service

