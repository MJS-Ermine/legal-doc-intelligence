"""Base classes for vector store implementations."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class BaseVectorStore(ABC):
    """Abstract base class for vector store implementations.
    
    This class defines the interface that all vector store implementations must follow.
    It provides methods for adding, searching, and managing document embeddings.
    """

    def __init__(self, persist_directory: Optional[Path] = None):
        """Initialize the vector store.
        
        Args:
            persist_directory: Optional directory path for persisting the vector store.
                If None, the store will be in-memory only.
        """
        self.persist_directory = persist_directory
        if persist_directory:
            persist_directory.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> List[str]:
        """Add texts and their metadata to the vector store.
        
        Args:
            texts: List of text strings to add.
            metadatas: Optional list of metadata dictionaries.
            **kwargs: Additional arguments specific to the implementation.
            
        Returns:
            List of IDs for the added texts.
        """
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Search for similar texts in the vector store.
        
        Args:
            query: Query text to search for.
            k: Number of results to return.
            **kwargs: Additional arguments specific to the implementation.
            
        Returns:
            List of dictionaries containing similar documents and their metadata.
        """
        pass

    @abstractmethod
    def persist(self) -> None:
        """Persist the vector store to disk if persistence is enabled."""
        pass

    @abstractmethod
    def load(self) -> None:
        """Load the vector store from disk if persistence is enabled."""
        pass
