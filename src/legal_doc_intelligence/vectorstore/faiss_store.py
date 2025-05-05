"""FAISS vector store implementation for the Legal Document Intelligence Platform."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer


class FAISSVectorStore:
    """Vector store for legal documents using FAISS."""

    def __init__(
        self,
        collection_name: str = "legal_documents",
        embedding_model_name: str = "paraphrase-multilingual-mpnet-base-v2",
        persist_directory: str = "./data/vectorstore"
    ) -> None:
        """Initialize the vector store.

        Args:
            collection_name: Name of the collection.
            embedding_model_name: Name of the sentence-transformers model to use.
            persist_directory: Directory to persist the vector store.
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # Initialize FAISS index
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)

        # Initialize document storage
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.ids: List[str] = []

        # Load existing data if available
        self._load_data()

        logger.info(f"Initialized FAISS vector store with collection '{collection_name}'")

    def _load_data(self) -> None:
        """Load existing data from disk."""
        index_path = self.persist_directory / f"{self.collection_name}.index"
        data_path = self.persist_directory / f"{self.collection_name}.json"

        if index_path.exists() and data_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.documents = data['documents']
                self.metadatas = data['metadatas']
                self.ids = data['ids']

    def _save_data(self) -> None:
        """Save data to disk."""
        index_path = self.persist_directory / f"{self.collection_name}.index"
        data_path = self.persist_directory / f"{self.collection_name}.json"

        faiss.write_index(self.index, str(index_path))
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump({
                'documents': self.documents,
                'metadatas': self.metadatas,
                'ids': self.ids
            }, f, ensure_ascii=False, indent=2)

    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add documents to the vector store.

        Args:
            documents: List of document texts to add.
            ids: List of unique IDs for the documents.
            metadatas: Optional list of metadata dictionaries for the documents.
        """
        try:
            if not metadatas:
                metadatas = [{"added_at": datetime.utcnow().isoformat()} for _ in documents]

            # Generate embeddings
            embeddings = self.embedding_model.encode(documents)

            # Add to FAISS index
            self.index.add(np.array(embeddings).astype('float32'))

            # Store document data
            self.documents.extend(documents)
            self.metadatas.extend(metadatas)
            self.ids.extend(ids)

            # Save to disk
            self._save_data()

            logger.info(f"Added {len(documents)} documents to vector store")

        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents.

        Args:
            query: Query text to search for.
            n_results: Number of results to return.
            where: Optional filter conditions (not implemented for FAISS).

        Returns:
            Dict containing search results with documents, distances, and metadata.
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])

            # Search in FAISS
            distances, indices = self.index.search(
                np.array(query_embedding).astype('float32'),
                k=n_results
            )

            # Gather results
            result_documents = [self.documents[i] for i in indices[0]]
            result_metadatas = [self.metadatas[i] for i in indices[0]]
            result_ids = [self.ids[i] for i in indices[0]]

            return {
                "documents": result_documents,
                "distances": distances[0].tolist(),
                "metadatas": result_metadatas,
                "ids": result_ids
            }

        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise

    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from the vector store.

        Args:
            ids: List of document IDs to delete.
        """
        try:
            # Find indices to delete
            indices_to_delete = [i for i, doc_id in enumerate(self.ids) if doc_id in ids]

            if not indices_to_delete:
                return

            # Create new index
            new_index = faiss.IndexFlatL2(self.dimension)

            # Get all vectors
            all_vectors = faiss.vector_to_array(self.index.reconstruct_n(0, self.index.ntotal))
            all_vectors = all_vectors.reshape(self.index.ntotal, self.dimension)

            # Remove deleted vectors
            mask = np.ones(len(self.ids), dtype=bool)
            mask[indices_to_delete] = False

            # Update index and metadata
            if np.any(mask):
                new_index.add(all_vectors[mask])
                self.documents = [doc for i, doc in enumerate(self.documents) if i not in indices_to_delete]
                self.metadatas = [
                    meta for i, meta in enumerate(self.metadatas)
                    if i not in indices_to_delete
                ]
                self.ids = [id for i, id in enumerate(self.ids) if i not in indices_to_delete]
            else:
                self.documents = []
                self.metadatas = []
                self.ids = []

            self.index = new_index
            self._save_data()

            logger.info(f"Deleted {len(ids)} documents from vector store")

        except Exception as e:
            logger.error(f"Error deleting documents from vector store: {str(e)}")
            raise

    def get_document(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID.

        Args:
            id: Document ID to retrieve.

        Returns:
            Dict containing document data if found, None otherwise.
        """
        try:
            if id in self.ids:
                idx = self.ids.index(id)
                return {
                    "document": self.documents[idx],
                    "metadata": self.metadatas[idx]
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving document from vector store: {str(e)}")
            raise
