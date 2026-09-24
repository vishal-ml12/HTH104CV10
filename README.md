# Multi-Waste-Stream Contamination & Recycling Yield Optimizer

A full-stack intelligent waste-stream analytics platform designed to assess material composition, contamination severity, and predict recycling yield.

> **Status:** Development Phase 1 Complete (Working Foundation & End-to-End Pipeline)

---

## Architecture (Phase 1)

```
React Frontend (Vite + Tailwind CSS)
        │
        ▼  [POST /api/analyze (multipart/form-data)]
FastAPI Backend (backend/routes/api.py)
        │
        ▼
Mock AI Analysis Service (backend/services/ai_service.py)
        │
        ▼
Recycling Yield & Quality Engine (backend/services/yield_service.py)
        │
        ▼
MySQL Database (waste_optimizer.waste_analysis)
        │
        ▼
Analysis Result JSON
        │
        ▼
React Frontend (Displays detection, quality, yield, and aggregate statistics)
```

### Architectural Decoupling Rule
The AI layer is strictly separated from backend business logic and API contracts:
- `backend/services/ai_service.py` defines the `BaseAIService` interface and the Phase 1 `MockAIService`.
- In Phase 2, the computer vision engine (`ai-model/` using YOLO / OpenCV) will implement this exact interface with zero rewrites needed in the backend routing, yield calculation, database, or frontend code.

---

## Project Structure

```
multi-waste-recycling-optimizer/
├── frontend/                     # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── App.jsx               # Test console interface
│   │   ├── index.css             # Tailwind CSS entrypoint
│   │   └── main.jsx
│   ├── vite.config.js            # Vite configuration with Tailwind plugin
│   └── package.json
├── backend/                      # FastAPI Backend
│   ├── main.py                   # FastAPI app entrypoint & CORS
│   ├── database/
│   │   ├── __init__.py
│   │   └── session.py            # SQLAlchemy engine, session & get_db
│   ├── models/
│   │   ├── __init__.py
│   │   └── waste_analysis.py     # SQLAlchemy model for waste_analysis
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── analysis.py           # Pydantic request & response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py         # Mock AI analysis service (decoupled)
│   │   └── yield_service.py      # Quality & yield calculation service
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py                # Health, analyze, results, statistics routes
│   ├── tests/
│   │   └── test_api.py           # Automated test suite
│   ├── .env                      # Local environment configuration
│   ├── .env.example
│   └── requirements.txt
├── ai-model/                     # Computer vision module (Phase 2 YOLO/OpenCV)
│   └── README.md
├── database/                     # Raw SQL schema
│   └── schema.sql
├── docs/                         # Architecture documentation
│   └── architecture.md
└── README.md
```

---

## Prerequisites

- **Python**: 3.10+
- **Node.js**: v18+ (tested on Node v24)
- **MySQL Server**: 8.0+

---

## Database Setup

1. Log into your MySQL instance:
   ```bash
   mysql -u root -p
   ```
2. Execute the schema script located at `database/schema.sql`:
   ```sql
   CREATE DATABASE IF NOT EXISTS waste_optimizer;
   USE waste_optimizer;

   CREATE TABLE IF NOT EXISTS waste_analysis (
       id INT AUTO_INCREMENT PRIMARY KEY,
       material VARCHAR(100) NOT NULL,
       confidence FLOAT NOT NULL,
       contamination_level VARCHAR(50) NOT NULL,
       contamination_percentage FLOAT NOT NULL,
       quality_score FLOAT NOT NULL,
       recycling_yield FLOAT NOT NULL,
       recommendation VARCHAR(255) NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       INDEX idx_created_at (created_at),
       INDEX idx_material (material)
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
   ```

---

## Backend Setup & Execution

1. Navigate to the backend directory and set up a virtual environment:
   ```powershell
   python -m venv backend/venv
   .\backend\venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. Configure environment variables in `backend/.env`:
   ```env
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=waste_optimizer
   DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/waste_optimizer
   ```
4. Start the FastAPI server:
   ```powershell
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Interactive Swagger documentation will be available at: `http://localhost:8000/docs`

---

## Frontend Setup & Execution

1. Navigate to the `frontend/` directory:
   ```powershell
   cd frontend
   ```
2. Install npm dependencies:
   ```powershell
   npm install
   ```
3. Start the Vite development server:
   ```powershell
   npm run dev
   ```
   The application will be accessible at: `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Returns service status (`{"status": "ok", "service": "Waste Recycling Optimizer"}`) |
| `POST` | `/api/analyze` | Accepts an optional image file upload, runs mock AI detection and yield computation, persists record into MySQL, and returns analysis response |
| `GET` | `/api/results` | Returns recent analysis records stored in MySQL |
| `GET` | `/api/statistics` | Returns aggregate statistics (`total_analyses`, `average_contamination`, `average_quality_score`, `average_recycling_yield`) |

---

## Testing & Verification

Run the automated backend test suite:
```powershell
.\backend\venv\Scripts\python backend/tests/test_api.py
```
Expected output:
```text
PASS: /api/health returned: {'status': 'ok', 'service': 'Waste Recycling Optimizer'}
PASS: /api/analyze (no file) returned: {'success': True, 'analysis': ...}
PASS: /api/analyze (with file upload) succeeded
PASS: /api/results returned stored records
PASS: /api/statistics returned aggregate statistics
--- ALL BACKEND TESTS PASSED SUCCESSFULLY! ---
```
