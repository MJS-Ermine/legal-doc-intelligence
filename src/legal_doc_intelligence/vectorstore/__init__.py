"""
Vector store module for legal document embeddings and retrieval.

This module provides functionality for:
- Document embedding generation
- Vector storage and retrieval
- Similarity search
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .faiss_store import FAISSVectorStore

__all__ = [
    "FAISSVectorStore"
]

def create_vector_store(
    collection_name: str = "legal_documents",
    embedding_model_name: str = "paraphrase-multilingual-mpnet-base-v2",
    persist_directory: Optional[str] = None,
    **kwargs: Dict[str, Any]
) -> FAISSVectorStore:
    """Create a vector store instance.

    Args:
        collection_name: Name of the collection.
        embedding_model_name: Name of the sentence-transformers model to use.
        persist_directory: Directory to persist the vector store.
        **kwargs: Additional arguments to pass to the vector store.

    Returns:
        An instance of FAISSVectorStore.
    """
    if persist_directory is None:
        persist_directory = os.path.join(os.getcwd(), "data", "vectorstore")

    return FAISSVectorStore(
        collection_name=collection_name,
        embedding_model_name=embedding_model_name,
        persist_directory=persist_directory,
        **kwargs
    )
