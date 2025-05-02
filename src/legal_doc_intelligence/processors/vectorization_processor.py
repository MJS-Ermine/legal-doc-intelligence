"""Processor for converting documents to vector representations."""

from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from ..database.models import Document, ProcessingRecord
from ..vectorstore import FAISSVectorStore


class VectorizationProcessor:
    """Processor for converting legal documents to vector representations."""

    def __init__(self, vector_store: FAISSVectorStore) -> None:
        """Initialize the vectorization processor.
        
        Args:
            vector_store: Instance of FAISSVectorStore for document storage.
        """
        self.vector_store = vector_store

    def process_document(self, document: Document, db: Session) -> None:
        """Process a single document and add it to the vector store.
        
        Args:
            document: Document instance to process.
            db: Database session.
        """
        try:
            # Create processing record
            processing_record = ProcessingRecord(
                document_id=document.id,
                processing_type="vectorization",
                status="in_progress"
            )
            db.add(processing_record)
            db.commit()

            # Prepare document metadata
            metadata = {
                "doc_type": document.doc_type.value,
                "court_name": document.court_name,
                "decision_date": document.decision_date.isoformat() if document.decision_date else None,
                "source_url": document.source_url,
                "db_id": document.id
            }

            if document.metadata:
                metadata.update({
                    "case_number": document.metadata.case_number,
                    "judge_names": document.metadata.judge_names,
                    "keywords": document.metadata.keywords,
                    "category": document.metadata.category,
                    "subcategory": document.metadata.subcategory
                })

            # Add document to vector store
            self.vector_store.add_documents(
                documents=[document.content],
                ids=[f"doc_{document.id}"],
                metadatas=[metadata]
            )

            # Update processing record
            processing_record.status = "success"
            db.commit()

            logger.info(f"Successfully vectorized document {document.id}")

        except Exception as e:
            if 'processing_record' in locals():
                processing_record.status = "failed"
                processing_record.error_message = str(e)
                db.commit()

            logger.error(f"Error vectorizing document {document.id}: {str(e)}")
            raise

    def process_documents(self, documents: List[Document], db: Session) -> None:
        """Process multiple documents and add them to the vector store.
        
        Args:
            documents: List of Document instances to process.
            db: Database session.
        """
        for document in documents:
            try:
                self.process_document(document, db)
            except Exception as e:
                logger.error(f"Failed to process document {document.id}: {str(e)}")
                continue

    def search_similar_documents(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents in the vector store.
        
        Args:
            query: Query text to search for.
            n_results: Number of results to return.
            filters: Optional filters to apply to the search (not implemented for FAISS).
            
        Returns:
            Dict containing search results.
        """
        try:
            if filters:
                logger.warning("Filters are not implemented for FAISS vector store")

            results = self.vector_store.search(
                query=query,
                n_results=n_results
            )

            return results

        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise
