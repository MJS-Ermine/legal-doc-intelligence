"""FastAPI application for legal document intelligence."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router

# Create FastAPI app
app = FastAPI(
    title="Legal Document Intelligence API",
    description="API for processing and searching legal documents",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include router
app.include_router(router)

# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
