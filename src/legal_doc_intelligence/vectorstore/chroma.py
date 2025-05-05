"""Chroma vector store implementation."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api import API as ChromaAPI
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .base import BaseVectorStore

logger = logging.getLogger(__name__)

class ChromaVectorStore(BaseVectorStore):
    """ChromaDB 向量資料庫實作，整合 sentence-transformers。"""

    def __init__(
        self,
        collection_name: str = "legal_documents",
        persist_directory: Optional[Path] = None,
        embedding_model: str = "shibing624/text2vec-base-chinese"
    ):
        """Initialize the Chroma vector store.

        Args:
            collection_name: Name of the Chroma collection to use.
            persist_directory: Optional directory path for persisting the vector store.
            embedding_model: Name or path of the SentenceTransformer model to use.
        """
        super().__init__(persist_directory)

        # Initialize Chroma client
        self.client: ChromaAPI = chromadb.Client(
            Settings(
                persist_directory=str(persist_directory) if persist_directory else None,
                is_persistent=persist_directory is not None
            )
        )

        # Initialize or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        logger.info(f"Initialized ChromaVectorStore with collection '{collection_name}'")

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
            **kwargs: Additional arguments passed to Chroma.

        Returns:
            List of IDs for the added texts.
        """
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts).tolist()

        # Generate IDs if not provided
        ids = kwargs.get("ids", [str(i) for i in range(len(texts))])

        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(texts)} documents to vector store")
        return ids

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
            **kwargs: Additional arguments passed to Chroma.

        Returns:
            List of dictionaries containing similar documents and their metadata.
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            **kwargs
        )

        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "id": results["ids"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            })

        logger.info(f"Found {len(formatted_results)} similar documents")
        return formatted_results

    def persist(self) -> None:
        """Persist the vector store to disk if persistence is enabled."""
        if self.persist_directory:
            self.client.persist()
            logger.info("Persisted vector store to disk")

    def load(self) -> None:
        """Load the vector store from disk if persistence is enabled."""
        # Chroma handles loading automatically when initializing the client
        if self.persist_directory:
            logger.info("Vector store loaded from disk")

    def add_documents(self, docs: List[Dict[str, Any]]) -> None:
        texts = [doc["content"] for doc in docs]
        embeddings = self.embedding_model.encode(texts)
        for doc, emb in zip(docs, embeddings, strict=False):
            self.collection.add(
                documents=[doc["content"]],
                metadatas=[doc.get("metadata", {})],
                embeddings=[emb.tolist()],
                ids=[str(doc["id"])]
            )

    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_emb = self.embedding_model.encode([query])[0].tolist()
        results = self.collection.query(query_embeddings=[query_emb], n_results=top_k)
        return results.get("documents", [])
