# Architecture Overview - Phase 1

## End-to-End Data Flow

```text
React Frontend (Vite + Tailwind)
       │
       ▼  (multipart/form-data POST /api/analyze)
FastAPI Backend (backend/routes/api.py)
       │
       ▼
Mock AI Analysis Service (backend/services/ai_service.py)
  - Identifies material and confidence (e.g. plastic 0.94)
  - Evaluates contamination (level: medium, percentage: 22%)
       │
       ▼
Yield Calculation Engine (backend/services/yield_service.py)
  - Calculates quality score (e.g. 78)
  - Calculates recycling yield (e.g. 78)
  - Generates operational recommendation
       │
       ▼
MySQL Database (waste_optimizer.waste_analysis)
  - Persists record with timestamp
       │
       ▼
API Response (JSON matching Phase 1 contract)
       │
       ▼
React Frontend displays results, history, and real-time statistics
```

## Architectural Decoupling
1. **AI Layer Isolation**: `backend/services/ai_service.py` implements `BaseAIService`. The backend business logic and API endpoints depend exclusively on the contract, allowing Phase 2 YOLO/OpenCV models to drop in seamlessly.
2. **Yield & Quality Engine**: Pure domain service isolated from computer vision perception.
3. **Storage Abstraction**: SQLAlchemy ORM models cleanly mapping domain entities to MySQL.
