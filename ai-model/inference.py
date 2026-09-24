"""
High-Level AI Inference API.

Provides unified entrypoints for both multi-object waste detection and legacy single-material queries.
"""

import sys
import os
from typing import Dict, Any, Optional

pkg_dir = os.path.dirname(os.path.abspath(__file__))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

try:
    from .adapter import get_vision_adapter, VisionModelAdapter
except (ImportError, ValueError):
    from adapter import get_vision_adapter, VisionModelAdapter


def run_inference(image_bytes: bytes) -> Dict[str, Any]:
    """
    Execute multi-object computer vision inference on input image bytes.

    Returns:
        Structured analysis dictionary:
        {
            "mode": "REAL_YOLO" | "DEMO_FALLBACK",
            "detected_objects": [...],
            "primary_material": str,
            "primary_confidence": float,
            "materials": [{"name": str, "confidence": float}],
            "contamination": {"level": str, "percentage": float},
            "image_dimensions": {"width": int, "height": int}
        }
    """
    adapter = get_vision_adapter()
    raw_result = adapter.detect(image_bytes)

    # Format materials array for compatibility
    materials = [
        {"name": obj["material"], "confidence": obj["confidence"]}
        for obj in raw_result["detected_objects"]
    ]

    return {
        "mode": raw_result.get("mode", adapter.mode),
        "detected_objects": raw_result["detected_objects"],
        "primary_material": raw_result["primary_material"],
        "primary_confidence": raw_result["primary_confidence"],
        "materials": materials,
        "contamination": {
            "level": raw_result["contamination_level"],
            "percentage": raw_result["contamination_percentage"],
        },
        "image_dimensions": raw_result.get("image_dimensions", {"width": 640, "height": 640}),
    }
