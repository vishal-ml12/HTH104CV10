"""
Image Preprocessing and Computer Vision Feature Extraction.

Prepares input images for the YOLO11n ONNX inference session and calculates
prototype visible contamination indicators from visual features.
"""

import io
from typing import Tuple
import numpy as np
from PIL import Image, ImageOps, ImageFilter


def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """Load image from raw bytes and convert to standard RGB mode."""
    image = Image.open(io.BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image)  # Correct orientation based on EXIF
    return image.convert("RGB")


def letterbox_image(image: Image.Image, target_size: int = 640) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    Resize image with aspect ratio preservation and letterbox padding for YOLO models.
    Returns:
        input_tensor: Normalized float32 array shaped (1, 3, target_size, target_size)
        scale: Scale factor applied
        pad: (pad_x, pad_y) tuple
    """
    orig_w, orig_h = image.size
    scale = min(target_size / orig_w, target_size / orig_h)
    new_w, new_h = max(1, int(round(orig_w * scale))), max(1, int(round(orig_h * scale)))

    resized = image.resize((new_w, new_h), Image.Resampling.BILINEAR)

    # 114 is standard neutral gray fill in YOLO
    canvas = Image.new("RGB", (target_size, target_size), (114, 114, 114))
    pad_x = (target_size - new_w) // 2
    pad_y = (target_size - new_h) // 2
    canvas.paste(resized, (pad_x, pad_y))

    # Convert to normalized float32 tensor
    arr = np.array(canvas, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))  # HWC -> CHW
    tensor = np.expand_dims(arr, axis=0)  # Shape: (1, 3, 640, 640)

    return tensor, scale, (pad_x, pad_y)


def estimate_visible_contamination(image: Image.Image) -> Tuple[str, float]:
    """
    Prototype visible contamination analysis:
    Computes visual edge/debris density and color variance across the sample image.

    IMPORTANT NOTE:
    This is a prototype estimated contamination heuristic derived from visual frequency
    and edge complexity in the image. It is separate from the material classification model
    and will be replaced by a fine-grained segmentation model in future phases.
    """
    # Convert to grayscale for edge analysis
    gray = image.convert("L").resize((256, 256), Image.Resampling.BILINEAR)
    
    # Detect high-frequency edges/particulates using Laplacian edge filter
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_data = np.array(edges, dtype=np.float32)

    # Ratio of strong edge pixels indicates surface debris, labels, or dirt
    edge_intensity = float(np.mean(edge_data))

    # Base scale: typical clean images have edge intensity 5-15, dirty/cluttered 30-70
    raw_percentage = (edge_intensity / 45.0) * 35.0

    # Clamp between realistic bounds (3.0% to 50.0%)
    contamination_pct = max(3.0, min(50.0, round(raw_percentage, 1)))

    if contamination_pct < 12.0:
        level = "low"
    elif contamination_pct < 28.0:
        level = "medium"
    else:
        level = "high"

    return level, contamination_pct


def estimate_object_crop_contamination(
    image: Image.Image,
    bbox: dict,
    material: str = "plastic"
) -> Tuple[str, str, float]:
    """
    Phase 2 Object-Level Contamination Analysis:
    Extracts the bounding box crop of a detected object and evaluates visually detectable
    contamination characteristics:
    - Label / adhesive presence
    - Organic or beverage residues
    - Cross-polymer contamination (e.g. PP cap / PE ring on PET bottle)
    - Particulate / soil / dust
    
    IMPORTANT DISCLAIMER:
    RGB camera computer vision analyzes surface visual characteristics only.
    Hidden or embedded chemical contaminants cannot be detected with standard RGB optics.
    """
    w, h = image.size
    norm = bbox.get("normalized", {})
    x1 = int(max(0, min(w - 1, norm.get("x", 0.0) / 100.0 * w)))
    y1 = int(max(0, min(h - 1, norm.get("y", 0.0) / 100.0 * h)))
    bw = int(max(4, min(w - x1, norm.get("width", 100.0) / 100.0 * w)))
    bh = int(max(4, min(h - y1, norm.get("height", 100.0) / 100.0 * h)))
    x2 = min(w, x1 + bw)
    y2 = min(h, y1 + bh)

    try:
        crop = image.crop((x1, y1, x2, y2)).resize((128, 128), Image.Resampling.BILINEAR)
    except Exception:
        return "none", "low", 5.0

    # Convert to RGB arrays
    rgb = np.array(crop, dtype=np.float32)
    gray = crop.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_mean = float(np.mean(np.array(edges, dtype=np.float32)))

    # Compute color variance across crop
    std_r = float(np.std(rgb[:, :, 0]))
    std_g = float(np.std(rgb[:, :, 1]))
    std_b = float(np.std(rgb[:, :, 2]))
    color_var = (std_r + std_g + std_b) / 3.0

    # Contamination percentage heuristic
    score_raw = (edge_mean * 0.45) + (color_var * 0.25)
    score_clamped = max(2.0, min(55.0, round(score_raw, 1)))

    # Classify visually detectable category based on material & color heuristics
    mat = material.lower()
    if score_clamped < 10.0:
        category = "none"
    elif mat == "plastic" and (std_r > 35.0 or std_b > 35.0):
        category = "label_adhesive" if edge_mean > 25.0 else "cross_polymer"
    elif mat in ["paper", "cardboard"] and (std_g > 30.0 or std_r > 30.0):
        category = "organic_residue"
    elif mat == "metal" and edge_mean > 30.0:
        category = "label_adhesive"
    elif mat == "glass" and (std_g > 25.0 or color_var > 30.0):
        category = "organic_residue"
    elif edge_mean > 32.0:
        category = "soil_dust"
    else:
        category = "organic_residue" if score_clamped > 25.0 else "none"

    if score_clamped < 15.0:
        severity = "low"
    elif score_clamped < 35.0:
        severity = "medium"
    elif score_clamped < 55.0:
        severity = "high"
    else:
        severity = "critical"

    return category, severity, score_clamped
