"""Script to run the FastAPI application."""

import logging
from pathlib import Path

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main() -> None:
    """Run the FastAPI application."""
    # Ensure vector store directory exists
    vector_store_dir = Path("data/vector_store")
    vector_store_dir.mkdir(parents=True, exist_ok=True)

    # Start server
    logger.info("Starting API server...")
    uvicorn.run(
        "legal_doc_intelligence.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
