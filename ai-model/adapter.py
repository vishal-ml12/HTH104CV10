"""
Vision Model Adapter Layer.

Maintains strict separation between the REAL YOLO Vision Model and the DEMO/FALLBACK simulator.
Allows seamless substitution of models while maintaining API contract integrity.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
import sys
import random
import hashlib

pkg_dir = os.path.dirname(os.path.abspath(__file__))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

try:
    from .classifier import WasteMaterialClassifier
    from .labels import MATERIAL_TO_STREAM
except (ImportError, ValueError):
    from classifier import WasteMaterialClassifier
    from labels import MATERIAL_TO_STREAM


class BaseVisionDetector(ABC):
    @abstractmethod
    def detect(self, image_bytes: bytes) -> Dict[str, Any]:
        """Run multi-object detection on image bytes."""
        pass

    @abstractmethod
    def get_mode_name(self) -> str:
        """Return human-readable mode identifier."""
        pass


class YOLO11VisionDetector(BaseVisionDetector):
    """Real YOLO11n Computer Vision Detector running on ONNX Runtime."""

    def __init__(self, model_path: Optional[str] = None):
        self.classifier = WasteMaterialClassifier(model_path=model_path)

    def detect(self, image_bytes: bytes) -> Dict[str, Any]:
        return self.classifier.detect_multiple_objects(image_bytes)

    def get_mode_name(self) -> str:
        return "REAL_YOLO"


class DemoFallbackVisionDetector(BaseVisionDetector):
    """
    DEMO FALLBACK SIMULATOR.

    Clearly declared as simulated test-harness when no neural network weights are available.
    Does NOT claim real accuracy.
    """

    def detect(self, image_bytes: bytes) -> Dict[str, Any]:
        # Generate simulated multi-object mixed stream for UI testing
        seed_int = int.from_bytes(hashlib.sha256(image_bytes).digest()[:4], "big")
        rng = random.Random(seed_int)

        sim_classes = ["plastic", "glass", "metal", "paper", "organic"]
        num_items = rng.randint(2, 4)

        objects = []
        for i in range(1, num_items + 1):
            mat = rng.choice(sim_classes)
            conf = round(rng.uniform(0.70, 0.95), 2)
            stream = MATERIAL_TO_STREAM.get(mat, "review")

            contam_categories = ["none", "label_adhesive", "organic_residue", "cross_polymer"]
            cat = rng.choice(contam_categories)
            c_score = round(rng.uniform(5.0, 28.0), 1) if cat != "none" else round(rng.uniform(2.0, 8.0), 1)
            c_sev = "low" if c_score < 15.0 else ("medium" if c_score < 35.0 else "high")

            objects.append({
                "object_id": f"sim_obj_{i}",
                "material": mat,
                "raw_class": mat,
                "confidence": conf,
                "confidence_level": "high" if conf >= 0.8 else "medium",
                "stream": stream,
                "status": "sorted",
                "contamination_category": cat,
                "contamination_severity": c_sev,
                "contamination_score": c_score,
                "bbox": {
                    "x": float(rng.randint(20, 200)),
                    "y": float(rng.randint(20, 200)),
                    "width": float(rng.randint(80, 250)),
                    "height": float(rng.randint(80, 250)),
                    "normalized": {
                        "x": float(rng.randint(5, 50)),
                        "y": float(rng.randint(5, 50)),
                        "width": float(rng.randint(20, 40)),
                        "height": float(rng.randint(20, 40)),
                    }
                }
            })

        primary = objects[0]
        return {
            "mode": "DEMO_FALLBACK",
            "detected_objects": objects,
            "primary_material": primary["material"],
            "primary_confidence": primary["confidence"],
            "contamination_level": "medium",
            "contamination_percentage": 18.0,
            "image_dimensions": {"width": 640, "height": 480},
        }

    def get_mode_name(self) -> str:
        return "DEMO_FALLBACK"


class VisionModelAdapter:
    """Factory and registry adapter selecting real YOLO vs demo fallback."""

    def __init__(self, force_demo: bool = False):
        self.detector: BaseVisionDetector
        model_file = os.path.join(os.path.dirname(__file__), "model", "mira_exp019.onnx")

        if not force_demo and os.path.exists(model_file):
            try:
                self.detector = YOLO11VisionDetector(model_path=model_file)
            except Exception as e:
                print(f"[Warning] Falling back to Demo detector: {e}")
                self.detector = DemoFallbackVisionDetector()
        else:
            self.detector = DemoFallbackVisionDetector()

    def detect(self, image_bytes: bytes) -> Dict[str, Any]:
        return self.detector.detect(image_bytes)

    @property
    def mode(self) -> str:
        return self.detector.get_mode_name()


# Global default adapter
global_adapter = VisionModelAdapter()


def get_vision_adapter() -> VisionModelAdapter:
    return global_adapter
