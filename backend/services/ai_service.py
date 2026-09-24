"""
AI Detection Service Layer.

Integrates the actual computer-vision waste classification model from the `ai-model` package.
All material classification is performed directly on image pixel data using the trained YOLO11
waste classification neural network.
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Ensure project root is in sys.path to import ai_model
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

ai_model_dir = os.path.join(project_root, "ai-model")
if ai_model_dir not in sys.path:
    sys.path.insert(0, ai_model_dir)

# Import the actual computer vision model inference engine
try:
    from importlib import import_module
    # Handle folder name with hyphen "ai-model"
    import importlib.util
    ai_model_path = os.path.join(project_root, "ai-model", "inference.py")
    spec = importlib.util.spec_from_file_location("ai_model_inference", ai_model_path)
    ai_model_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ai_model_module)
    run_cv_inference = ai_model_module.run_inference
    MODEL_AVAILABLE = True
except Exception as e:
    run_cv_inference = None
    MODEL_AVAILABLE = False
    _model_load_error = str(e)


class BaseAIService(ABC):
    @abstractmethod
    def detect_waste_and_contamination(
        self,
        image_bytes: Optional[bytes] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image for waste materials and contamination level.
        Returns a dictionary containing materials and contamination information.
        """
        pass


class VisionWasteAIService(BaseAIService):
    """
    Real Computer Vision AI Service.
    Uses the trained MIRA-AI YOLO11n ONNX model to analyze uploaded waste image pixels.
    DOES NOT use hashes, filenames, or hardcoded profiles to decide material.
    """

    def detect_waste_and_contamination(
        self,
        image_bytes: Optional[bytes] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        if not image_bytes or len(image_bytes) == 0:
            raise ValueError("No image bytes provided for computer vision analysis.")

        if not MODEL_AVAILABLE or run_cv_inference is None:
            raise RuntimeError(
                "AI model is not available. Please check model configuration."
            )

        # Run actual computer vision inference on image bytes
        return run_cv_inference(image_bytes)


# Active service instance configured with the real vision model
ai_service: BaseAIService = VisionWasteAIService()
MockAIService = VisionWasteAIService


def get_ai_service() -> BaseAIService:
    """Dependency provider for AI Service"""
    return ai_service
