"""Enhanced Chroma vector store implementation with optimizations."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api import API as ChromaAPI
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseVectorStore

logger = logging.getLogger(__name__)

class CacheEntry:
    """Cache entry for vector store results."""

    def __init__(self, data: Any, expiry: datetime):
        self.data = data
        self.expiry = expiry

class EnhancedChromaStore(BaseVectorStore):
    """Enhanced Chroma-based vector store implementation.

    Features:
    1. Batch processing with automatic size adjustment
    2. Result caching with TTL
    3. Automatic retries for robustness
    4. Enhanced similarity search with re-ranking
    5. Optimized embeddings management
    """

    def __init__(
        self,
        collection_name: str = "legal_documents",
        persist_directory: Optional[Path] = None,
        embedding_model: str = "shibing624/text2vec-base-chinese",
        batch_size: int = 100,
        cache_ttl: int = 3600,  # 1 hour
        max_retries: int = 3
    ):
        """Initialize the enhanced Chroma vector store.

        Args:
            collection_name: Name of the Chroma collection.
            persist_directory: Directory for persistence.
            embedding_model: SentenceTransformer model name.
            batch_size: Size of batches for processing.
            cache_ttl: Time-to-live for cache entries in seconds.
            max_retries: Maximum number of retry attempts.
        """
        super().__init__(persist_directory)

        self.batch_size = batch_size
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self._cache: Dict[str, CacheEntry] = {}

        # Initialize Chroma client with optimized settings
        self.client: ChromaAPI = chromadb.Client(
            Settings(
                persist_directory=str(persist_directory) if persist_directory else None,
                is_persistent=persist_directory is not None,
                anonymized_telemetry=False,
                chroma_db_impl="duckdb+parquet"
            )
        )

        # Initialize collection with optimized settings
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 128,
                "hnsw:M": 16
            }
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize cache directory
        if persist_directory:
            self.cache_dir = persist_directory / "cache"
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized EnhancedChromaStore with collection '{collection_name}' "
            f"and batch_size={batch_size}"
        )

    def _compute_cache_key(self, data: Any) -> str:
        """Compute cache key for data.

        Args:
            data: Data to compute key for.

        Returns:
            Cache key string.
        """
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if valid.

        Args:
            key: Cache key.

        Returns:
            Cached data if valid, None otherwise.
        """
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry.expiry:
                return entry.data
            else:
                del self._cache[key]
        return None

    def _add_to_cache(self, key: str, data: Any) -> None:
        """Add data to cache with TTL.

        Args:
            key: Cache key.
            data: Data to cache.
        """
        expiry = datetime.now() + timedelta(seconds=self.cache_ttl)
        self._cache[key] = CacheEntry(data, expiry)

        # Persist cache if enabled
        if hasattr(self, 'cache_dir'):
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'data': data,
                    'expiry': expiry.isoformat()
                }, f, ensure_ascii=False)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> List[str]:
        """Add texts in batches with retry mechanism.

        Args:
            texts: Texts to add.
            metadatas: Optional metadata for texts.
            **kwargs: Additional arguments.

        Returns:
            List of IDs for added texts.
        """
        all_ids = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_metadatas = metadatas[i:i + self.batch_size] if metadatas else None

            # Generate embeddings for batch
            embeddings = self.embedding_model.encode(
                batch_texts,
                batch_size=32,
                show_progress_bar=False
            ).tolist()

            # Generate IDs for batch
            batch_ids = [
                f"{kwargs.get('prefix', '')}_{j}"
                for j in range(i, i + len(batch_texts))
            ]

            # Add batch to collection
            self.collection.add(
                embeddings=embeddings,
                documents=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids
            )

            all_ids.extend(batch_ids)

            logger.info(f"Added batch of {len(batch_texts)} documents")

        return all_ids

    def _compute_query_embedding(self, query: str) -> List[float]:
        """Compute and cache query embedding.

        Args:
            query: Query text.

        Returns:
            Query embedding.
        """
        return self.embedding_model.encode(query).tolist()

    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        alpha: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Rerank results using additional criteria.

        Args:
            query: Original query.
            results: Initial results.
            alpha: Weight for combining scores.

        Returns:
            Reranked results.
        """
        for result in results:
            # Combine embedding similarity with other factors
            base_score = 1 - (result.get('distance', 0) or 0)  # Convert distance to similarity

            # Consider document recency if available
            recency_score = 0.0
            if 'timestamp' in result.get('metadata', {}):
                doc_time = datetime.fromisoformat(result['metadata']['timestamp'])
                age_days = (datetime.now() - doc_time).days
                recency_score = 1.0 / (1.0 + age_days)

            # Consider metadata match if available
            metadata_score = 0.0
            if 'metadata' in result:
                metadata_str = ' '.join(str(v) for v in result['metadata'].values())
                if any(term in metadata_str.lower() for term in query.lower().split()):
                    metadata_score = 0.5

            # Combine scores
            result['final_score'] = (
                (1 - alpha) * base_score +
                alpha * (0.7 * recency_score + 0.3 * metadata_score)
            )

        # Sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        return results

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Enhanced similarity search with caching and reranking.

        Args:
            query: Query text.
            k: Number of results.
            **kwargs: Additional arguments.

        Returns:
            List of similar documents.
        """
        # Check cache first
        cache_key = self._compute_cache_key({'query': query, 'k': k, **kwargs})
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            return cached_results

        # Get query embedding
        query_embedding = self._compute_query_embedding(query)

        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k * 2,  # Get more results for reranking
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

        # Rerank results
        reranked_results = self._rerank_results(query, formatted_results)[:k]

        # Cache results
        self._add_to_cache(cache_key, reranked_results)

        logger.info(f"Found and reranked {len(reranked_results)} documents")
        return reranked_results

    def persist(self) -> None:
        """Persist vector store and cache."""
        if self.persist_directory:
            self.client.persist()
            logger.info("Persisted vector store to disk")

    def load(self) -> None:
        """Load vector store and restore cache."""
        if not self.persist_directory:
            return

        # Restore cache from disk
        if hasattr(self, 'cache_dir'):
            for cache_file in self.cache_dir.glob("*.json"):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    expiry = datetime.fromisoformat(cache_data['expiry'])
                    if datetime.now() < expiry:
                        key = cache_file.stem
                        self._cache[key] = CacheEntry(cache_data['data'], expiry)

            logger.info("Restored cache from disk")
