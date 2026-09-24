# Computer Vision Waste Classification Model

## Model Overview
- **Model Name:** MIRA-AI YOLO11n Waste-Detection & Material Classifier (`mira_exp019.onnx`)
- **Model Architecture:** YOLO11n exported to ONNX format
- **Runtime Engine:** `onnxruntime` (CPU Execution Provider)
- **Model File:** `ai-model/model/mira_exp019.onnx` (~10.12 MB)
- **Training Origin:** Actually trained specifically for waste and recycling material sorting.
- **Training Datasets:** `dmedhi + TACO + Roboflow + TrashNet` (5,108 training images, 120 epochs, map50: 90.58%, precision: 87.2%, recall: 84.6%).

---

## Supported Material Classes

| System Standard Class | Model Raw Class | Description |
|---|---|---|
| `plastic` | `plastic` | Plastic bottles, containers, bags, polymers |
| `paper` | `paper` | Paper sheets, cardboard boxes, packaging |
| `metal` | `metal` | Aluminum cans, tin, scrap metal |
| `glass` | `glass` | Glass bottles, jars, cullet |
| `mixed_waste` | `trash` | Multi-material, complex packaging, composite refuse |
| `unknown` | *Thresholded* | Low-confidence detections (<50%) requiring manual sorting |

---

## Preprocessing Pipeline
1. **Image Loading**: Decodes raw image bytes via Pillow into 3-channel RGB.
2. **Letterbox Resizing**: Scales the image preserving original aspect ratio into a $640 \times 640$ canvas with neutral gray padding ($114, 114, 114$).
3. **Normalization**: Rescales pixel values to $[0.0, 1.0]$ float32 and transposes from HWC to CHW format: `(1, 3, 640, 640)`.
4. **Inference**: Single forward pass producing shape `(1, 9, 8400)` spanning 8,400 multi-scale anchor boxes across 5 waste classes.
5. **Confidence Thresholding**:
   - $\ge 80\%$: High confidence (accepted directly).
   - $50\% - 79\%$: Medium confidence (accepted with verification notice).
   - $< 50\%$: Low confidence (flagged as `unknown` with manual verification recommendation).

---

## Contamination and Quality Analysis
- **Visible Contamination Heuristic**: Prototype visual edge and high-frequency noise analysis (evaluates foreign particulate and surface debris density).
- **Quality Score**: Derived as $100.0 - \text{contamination\_percentage}$ ($0\text{--}100$).
- **Recycling Yield**: Derived from material base recovery factor minus contamination penalty factor:
  $$\text{Yield} = \text{BaseRecovery}(\text{material}) - (\text{contamination} \times 0.85)$$
- **Recommendation Engine**: Automatically recommends direct recycling, pre-processing, intensive decontamination, or manual verification based on classification confidence and contamination severity.
