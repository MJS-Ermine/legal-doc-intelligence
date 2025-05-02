"""Database models for the Legal Document Intelligence Platform."""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class DocumentType(enum.Enum):
    """Enumeration of supported document types."""

    COURT_DECISION = "court_decision"
    REGULATION = "regulation"
    ADMINISTRATIVE_RULE = "administrative_rule"


class Document(Base):
    """Model representing a legal document."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    doc_type = Column(Enum(DocumentType), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(2000), nullable=False)
    source_id = Column(String(100), nullable=True)  # Original ID from source
    court_name = Column(String(100), nullable=True)
    decision_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    doc_metadata = relationship("DocumentMetadata", back_populates="document", uselist=False)
    processing_records = relationship("ProcessingRecord", back_populates="document")

    def __repr__(self) -> str:
        """Return string representation of the document."""
        return f"<Document(id={self.id}, title={self.title[:30]}...)>"


class DocumentMetadata(Base):
    """Model for storing additional metadata about a document."""

    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    case_number = Column(String(100), nullable=True)
    judge_names = Column(String(500), nullable=True)
    keywords = Column(String(1000), nullable=True)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="doc_metadata")

    def __repr__(self) -> str:
        """Return string representation of the metadata."""
        return f"<DocumentMetadata(id={self.id}, document_id={self.document_id})>"


class ProcessingRecord(Base):
    """Model for tracking document processing history."""

    __tablename__ = "processing_records"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    processing_type = Column(String(50), nullable=False)  # e.g., "scraping", "cleaning", "analysis"
    status = Column(String(20), nullable=False)  # "success", "failed", "in_progress"
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="processing_records")

    def __repr__(self) -> str:
        """Return string representation of the processing record."""
        return f"<ProcessingRecord(id={self.id}, document_id={self.document_id}, type={self.processing_type})>"
