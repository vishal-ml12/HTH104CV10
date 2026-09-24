import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.session import Base, engine
from backend.routes.api import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waste_optimizer")

# Initialize database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error creating database tables on startup: {e}")

app = FastAPI(
    title="Multi-Waste-Stream Contamination & Recycling Yield Optimizer",
    version="1.0.0",
    description="Phase 1 Backend API providing waste classification, contamination assessment, and recycling yield optimization."
)

# CORS configuration for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "service": "Waste Recycling Optimizer API",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
