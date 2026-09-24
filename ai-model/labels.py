"""
Waste Material Classification Labels and Mappings.

Centralized definition of supported material classes, virtual sorting streams,
and confidence thresholds for the Waste Recycling Optimizer.
"""

from typing import Dict, List

# Primary standardized material classes
MATERIAL_CLASSES: List[str] = [
    "plastic",
    "glass",
    "metal",
    "paper",
    "organic",
    "mixed_waste",
    "unknown"
]

# Supported Virtual Sorting Streams
VIRTUAL_STREAMS: List[str] = [
    "plastic",
    "glass",
    "metal",
    "paper",
    "organic",
    "review"
]

# Raw class names from the trained MIRA-AI YOLO11 waste detection model
MODEL_RAW_CLASSES: List[str] = [
    "glass",
    "metal",
    "paper",
    "plastic",
    "trash"
]

# Mapping from raw model class names to standard system classes
MODEL_CLASS_MAPPING: Dict[str, str] = {
    "plastic": "plastic",
    "paper": "paper",
    "metal": "metal",
    "glass": "glass",
    "trash": "mixed_waste",
}

# Mapping from standard material class to designated virtual stream
MATERIAL_TO_STREAM: Dict[str, str] = {
    "plastic": "plastic",
    "glass": "glass",
    "metal": "metal",
    "paper": "paper",
    "cardboard": "paper",
    "organic": "organic",
    "food": "organic",
    "mixed_waste": "review",
    "unknown": "review",
}

# Configurable confidence thresholds
CONFIDENCE_HIGH_THRESHOLD: float = 0.80
CONFIDENCE_MEDIUM_THRESHOLD: float = 0.50
NMS_IOU_THRESHOLD: float = 0.45
DETECTION_CONF_THRESHOLD: float = 0.25
