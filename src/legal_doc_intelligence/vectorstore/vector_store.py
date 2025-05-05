"""Vector store implementation for the Legal Document Intelligence Platform."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions
from loguru import logger


class LegalVectorStore:
    """Vector store for legal documents using ChromaDB."""

    def __init__(
        self,
        collection_name: str = "legal_documents",
        embedding_model_name: str = "paraphrase-multilingual-mpnet-base-v2",
        persist_directory: str = "./data/vectorstore"
    ) -> None:
        """Initialize the vector store.

        Args:
            collection_name: Name of the ChromaDB collection.
            embedding_model_name: Name of the sentence-transformers model to use.
            persist_directory: Directory to persist the vector store.
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"created_at": datetime.utcnow().isoformat()}
        )

        logger.info(f"Initialized vector store with collection '{collection_name}'")

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

            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
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
            where: Optional filter conditions.

        Returns:
            Dict containing search results with documents, distances, and metadata.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )

            return {
                "documents": results["documents"][0],
                "distances": results["distances"][0],
                "metadatas": results["metadatas"][0],
                "ids": results["ids"][0]
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
            self.collection.delete(ids=ids)
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
            results = self.collection.get(ids=[id])
            if results["documents"]:
                return {
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving document from vector store: {str(e)}")
            raise
