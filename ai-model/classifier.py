"""
Waste Material Classifier Engine.

Executes ONNX Runtime multi-object detection inference using the trained
MIRA-AI YOLO11n model. Decodes multi-scale anchor boxes, applies Non-Maximum
Suppression (NMS), and maps detected items to material classes and virtual sorting streams.
"""

import sys
import os
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import onnxruntime as ort
from PIL import Image

pkg_dir = os.path.dirname(os.path.abspath(__file__))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

try:
    from .labels import (
        MODEL_RAW_CLASSES,
        MODEL_CLASS_MAPPING,
        MATERIAL_TO_STREAM,
        CONFIDENCE_HIGH_THRESHOLD,
        CONFIDENCE_MEDIUM_THRESHOLD,
        NMS_IOU_THRESHOLD,
        DETECTION_CONF_THRESHOLD,
    )
    from .preprocessing import (
        load_image_from_bytes,
        letterbox_image,
        estimate_visible_contamination,
        estimate_object_crop_contamination,
    )
except ImportError:
    from labels import (
        MODEL_RAW_CLASSES,
        MODEL_CLASS_MAPPING,
        MATERIAL_TO_STREAM,
        CONFIDENCE_HIGH_THRESHOLD,
        CONFIDENCE_MEDIUM_THRESHOLD,
        NMS_IOU_THRESHOLD,
        DETECTION_CONF_THRESHOLD,
    )
    from preprocessing import (
        load_image_from_bytes,
        letterbox_image,
        estimate_visible_contamination,
        estimate_object_crop_contamination,
    )


def run_nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.45) -> List[int]:
    """
    Standard Non-Maximum Suppression to eliminate duplicate overlapping bounding boxes.
    """
    if len(boxes) == 0:
        return []

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        union = areas[i] + areas[order[1:]] - inter
        ovr = np.where(union > 0, inter / union, 0.0)

        inds = np.where(ovr <= iou_threshold)[0]
        order = order[inds + 1]

    return keep


class WasteMaterialClassifier:
    """
    Real Computer Vision Multi-Object Waste Material Classifier.
    Runs YOLO11n ONNX inference on preprocessed image tensors to detect and classify
    multiple items in mixed-waste streams.
    """

    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, "model", "mira_exp019.onnx")

        self.model_path = model_path
        self.session: Optional[ort.InferenceSession] = None
        self.mode = "REAL_YOLO"
        self._load_model()

    def _load_model(self):
        """Initialize the ONNX inference session."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"AI model file not found at: {self.model_path}. "
                "Please ensure the model weights are downloaded."
            )
        try:
            self.session = ort.InferenceSession(
                self.model_path,
                providers=["CPUExecutionProvider"]
            )
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ONNX model: {str(e)}")

    def is_available(self) -> bool:
        """Check whether the classifier session is ready for inference."""
        return self.session is not None

    def detect_multiple_objects(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Run multi-object detection inference on uploaded image bytes.

        Returns:
            Dictionary containing:
                - detected_objects: list of object dictionaries with bounding boxes
                - primary_material: dominant material
                - confidence: confidence of primary material
                - contamination_level: 'low', 'medium', or 'high'
                - contamination_percentage: estimated visual contamination
                - mode: 'REAL_YOLO'
        """
        if not self.is_available():
            raise RuntimeError("AI model is not available. Please check model configuration.")

        # 1. Load image and letterbox to 640x640
        image = load_image_from_bytes(image_bytes)
        orig_w, orig_h = image.size
        input_tensor, scale, (pad_x, pad_y) = letterbox_image(image, target_size=640)

        # 2. Forward pass through YOLO11n ONNX
        outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
        preds = outputs[0][0].T  # Shape: [8400, 9]

        boxes_raw = preds[:, :4]    # cx, cy, w, h
        scores_raw = preds[:, 4:9]  # 5 classes: glass, metal, paper, plastic, trash
        class_ids = np.argmax(scores_raw, axis=1)
        confidences = np.max(scores_raw, axis=1)

        # 3. Filter by detection confidence threshold
        mask = confidences >= DETECTION_CONF_THRESHOLD
        detected_items: List[Dict[str, Any]] = []

        if np.any(mask):
            filtered_boxes = boxes_raw[mask]
            filtered_conf = confidences[mask]
            filtered_classes = class_ids[mask]

            # Coordinate transformation back to original image space
            cx = filtered_boxes[:, 0]
            cy = filtered_boxes[:, 1]
            w = filtered_boxes[:, 2]
            h = filtered_boxes[:, 3]

            x1 = np.maximum(0.0, (cx - w / 2.0 - pad_x) / scale)
            y1 = np.maximum(0.0, (cy - h / 2.0 - pad_y) / scale)
            x2 = np.minimum(float(orig_w), (cx + w / 2.0 - pad_x) / scale)
            y2 = np.minimum(float(orig_h), (cy + h / 2.0 - pad_y) / scale)
            boxes_scaled = np.stack([x1, y1, x2, y2], axis=1)

            # 4. Apply Non-Maximum Suppression (NMS)
            keep_indices = run_nms(boxes_scaled, filtered_conf, iou_threshold=NMS_IOU_THRESHOLD)

            for rank, idx in enumerate(keep_indices, 1):
                cid = int(filtered_classes[idx])
                raw_class = MODEL_RAW_CLASSES[cid]
                raw_conf = float(filtered_conf[idx])
                box = boxes_scaled[idx]
                bx = float(round(box[0], 1))
                by = float(round(box[1], 1))
                bw = float(round(max(1.0, box[2] - box[0]), 1))
                bh = float(round(max(1.0, box[3] - box[1]), 1))

                # Normalize to percentage [0-100] for responsive frontend overlays
                norm_x = round((bx / orig_w) * 100.0, 2)
                norm_y = round((by / orig_h) * 100.0, 2)
                norm_w = round((bw / orig_w) * 100.0, 2)
                norm_h = round((bh / orig_h) * 100.0, 2)

                # Standardize material name
                std_material = MODEL_CLASS_MAPPING.get(raw_class, "unknown")

                # Confidence tiering
                if raw_conf < CONFIDENCE_MEDIUM_THRESHOLD:
                    final_material = "unknown"
                    conf_level = "low"
                    stream = "review"
                    status = "pending_review"
                elif raw_conf < CONFIDENCE_HIGH_THRESHOLD:
                    final_material = std_material
                    conf_level = "medium"
                    stream = MATERIAL_TO_STREAM.get(std_material, "review")
                    status = "sorted"
                else:
                    final_material = std_material
                    conf_level = "high"
                    stream = MATERIAL_TO_STREAM.get(std_material, "review")
                    status = "sorted"

                detected_items.append({
                    "object_id": f"obj_{rank}",
                    "material": final_material,
                    "raw_class": raw_class,
                    "confidence": round(raw_conf, 2),
                    "confidence_level": conf_level,
                    "stream": stream,
                    "status": status,
                    "bbox": {
                        "x": bx,
                        "y": by,
                        "width": bw,
                        "height": bh,
                        "normalized": {
                            "x": norm_x,
                            "y": norm_y,
                            "width": norm_w,
                            "height": norm_h,
                        }
                    }
                })

        # 5. Fallback: If no anchor passed the detection threshold, take top candidate
        if len(detected_items) == 0:
            top_anchor_idx = int(np.argmax(confidences))
            top_cid = int(class_ids[top_anchor_idx])
            top_conf = float(confidences[top_anchor_idx])
            raw_class = MODEL_RAW_CLASSES[top_cid]
            std_mat = MODEL_CLASS_MAPPING.get(raw_class, "unknown")

            final_material = std_mat if top_conf >= CONFIDENCE_MEDIUM_THRESHOLD else "unknown"
            conf_tier = "low" if top_conf < CONFIDENCE_MEDIUM_THRESHOLD else "medium"
            stream = MATERIAL_TO_STREAM.get(final_material, "review")

            detected_items.append({
                "object_id": "obj_1",
                "material": final_material,
                "raw_class": raw_class,
                "confidence": round(top_conf, 2),
                "confidence_level": conf_tier,
                "stream": stream,
                "status": "pending_review" if conf_tier == "low" else "sorted",
                "bbox": {
                    "x": 0.0,
                    "y": 0.0,
                    "width": float(orig_w),
                    "height": float(orig_h),
                    "normalized": {
                        "x": 0.0,
                        "y": 0.0,
                        "width": 100.0,
                        "height": 100.0,
                    }
                }
            })

        # 6. Object-level contamination analysis
        for it in detected_items:
            cat, sev, score = estimate_object_crop_contamination(image, it["bbox"], it["material"])
            it["contamination_category"] = cat
            it["contamination_severity"] = sev
            it["contamination_score"] = score

        # 7. Primary material selection based on highest-confidence detection
        primary_item = max(detected_items, key=lambda x: x["confidence"])
        contam_level, contam_pct = estimate_visible_contamination(image)

        return {
            "mode": "REAL_YOLO",
            "detected_objects": detected_items,
            "primary_material": primary_item["material"],
            "primary_confidence": primary_item["confidence"],
            "contamination_level": contam_level,
            "contamination_percentage": contam_pct,
            "image_dimensions": {"width": orig_w, "height": orig_h},
        }

    # Backward compatibility wrapper for single-object classifier calls
    def classify_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        multi_res = self.detect_multiple_objects(image_bytes)
        primary = multi_res["detected_objects"][0]
        return {
            "material": primary["material"],
            "raw_class": primary.get("raw_class", primary["material"]),
            "confidence": primary["confidence"],
            "confidence_level": primary["confidence_level"],
            "contamination_level": multi_res["contamination_level"],
            "contamination_percentage": multi_res["contamination_percentage"],
            "mode": multi_res["mode"],
        }
