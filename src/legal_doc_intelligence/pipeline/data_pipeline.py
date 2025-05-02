"""Data pipeline for legal document processing."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database.models import Document, ProcessingRecord
from ..processors.document_processor import DocumentMetadata, DocumentProcessor
from ..processors.legal_document_validator import LegalDocumentValidator
from ..processors.legal_processor import LegalProcessor
from ..processors.pii_processor import PIIMaskingConfig
from ..processors.source_tracker import SourceTracker, SourceType
from ..processors.system_monitor import SystemMonitor
from ..processors.vectorization_processor import VectorizationProcessor

logger = logging.getLogger(__name__)

class PipelineStage(str, Enum):
    """Enumeration of pipeline stages."""

    # Basic stages
    INGESTION = "ingestion"
    CLEANING = "cleaning"
    PII_PROCESSING = "pii_processing"
    VECTORIZATION = "vectorization"
    VALIDATION = "validation"
    STORAGE = "storage"

    # Legal processing stages
    CITATION_EXTRACTION = "citation_extraction"
    TERM_STANDARDIZATION = "term_standardization"
    ARGUMENT_EXTRACTION = "argument_extraction"
    TIMELINE_CONSTRUCTION = "timeline_construction"
    PARTY_ANALYSIS = "party_analysis"

    # Quality control stages
    FORMAT_VALIDATION = "format_validation"
    CONTENT_VALIDATION = "content_validation"
    METADATA_VALIDATION = "metadata_validation"
    CONSISTENCY_CHECK = "consistency_check"
    COMPLETENESS_CHECK = "completeness_check"

class PipelineStatus(str, Enum):
    """Enumeration of pipeline status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"

@dataclass
class PipelineStats:
    """Statistics for pipeline execution."""

    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_stage: Optional[PipelineStage] = None

class PipelineConfig(BaseModel):
    """Configuration for data pipeline."""

    chunk_size: int = 500
    chunk_overlap: int = 50
    max_workers: int = 4
    batch_size: int = 100
    pii_config: Optional[PIIMaskingConfig] = None
    source_tracking: bool = True
    persist_intermediate: bool = True
    validation_rules: Dict[str, Any] = Field(default_factory=dict)

class DataPipeline:
    """Pipeline for processing legal documents.
    
    Features:
    1. Multi-stage document processing
    2. Parallel processing support
    3. Progress tracking and statistics
    4. Error handling and recovery
    5. Intermediate results persistence
    """

    def __init__(
        self,
        config: PipelineConfig,
        document_processor: DocumentProcessor,
        vectorization_processor: VectorizationProcessor,
        persist_dir: Optional[Path] = None
    ):
        """Initialize the data pipeline.
        
        Args:
            config: Pipeline configuration.
            document_processor: Document processor instance.
            vectorization_processor: Vectorization processor instance.
            persist_dir: Directory for persistence.
        """
        self.config = config
        self.document_processor = document_processor
        self.vectorization_processor = vectorization_processor
        self.persist_dir = persist_dir

        if persist_dir:
            self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.source_tracker = (
            SourceTracker(storage_dir=persist_dir / "sources")
            if config.source_tracking
            else None
        )

        self.stats = PipelineStats()
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)

        # Initialize new components
        self.legal_processor = LegalProcessor()
        self.validator = LegalDocumentValidator()
        self.monitor = SystemMonitor()

        logger.info(
            f"Initialized DataPipeline with max_workers={config.max_workers}, "
            f"batch_size={config.batch_size}"
        )

    async def _process_document(
        self,
        document: Union[str, Document],
        metadata: Optional[DocumentMetadata] = None,
        db: Optional[Session] = None
    ) -> Optional[str]:
        """Process a single document through the pipeline.
        
        Args:
            document: Document to process.
            metadata: Optional document metadata.
            db: Optional database session.
            
        Returns:
            Document ID if successful.
        """
        start_time = time.time()
        stage_start_time = start_time
        current_stage = PipelineStage.INGESTION

        try:
            # Update stats
            self.stats.total_documents += 1

            # Stage: Ingestion
            self.stats.current_stage = PipelineStage.INGESTION
            if isinstance(document, str):
                doc_content = document
                if not metadata:
                    metadata = DocumentMetadata(
                        doc_id=str(uuid4()),
                        case_type="unknown",
                        court="unknown",
                        date=datetime.now(),
                        source="direct",
                        title="Untitled Document"
                    )
            else:
                doc_content = document.content
                metadata = DocumentMetadata(
                    doc_id=str(document.id),
                    case_type=document.doc_type.value,
                    court=document.court_name or "unknown",
                    date=document.decision_date or datetime.now(),
                    source=document.source_url,
                    title=document.title
                )

            # Stage: Cleaning
            self.stats.current_stage = PipelineStage.CLEANING
            cleaned_text = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.document_processor._clean_text,
                doc_content
            )

            # Stage: PII Processing
            self.stats.current_stage = PipelineStage.PII_PROCESSING
            if self.config.pii_config:
                cleaned_text, pii_matches = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.document_processor.pii_processor.mask_pii,
                    cleaned_text
                )

            # Stage: Vectorization
            self.stats.current_stage = PipelineStage.VECTORIZATION
            if isinstance(document, Document) and db:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.vectorization_processor.process_document,
                    document,
                    db
                )

            # Stage: Format Validation
            current_stage = PipelineStage.FORMAT_VALIDATION
            stage_start_time = time.time()
            validation_results = self.validator.validate_format(doc_content)
            self._record_stage_completion(current_stage, stage_start_time)

            # Stage: Content Validation
            current_stage = PipelineStage.CONTENT_VALIDATION
            stage_start_time = time.time()
            validation_results.extend(self.validator.validate_content(doc_content))
            self._record_stage_completion(current_stage, stage_start_time)

            # Stage: Metadata Validation
            current_stage = PipelineStage.METADATA_VALIDATION
            stage_start_time = time.time()
            if metadata:
                validation_results.extend(
                    self.validator.validate_metadata(metadata.dict())
                )
            self._record_stage_completion(current_stage, stage_start_time)

            # Record validation errors
            for result in validation_results:
                if result.level == ValidationLevel.ERROR:
                    self.monitor.record_validation_error(
                        result.rule_name,
                        result.level.value
                    )

            # Stage: Legal Processing
            # Citation Extraction
            current_stage = PipelineStage.CITATION_EXTRACTION
            stage_start_time = time.time()
            processed_text, extracted_info, processing_results = (
                self.legal_processor.process_document(doc_content)
            )
            self._record_stage_completion(current_stage, stage_start_time)

            # Term Standardization
            current_stage = PipelineStage.TERM_STANDARDIZATION
            stage_start_time = time.time()
            standardized_text, term_replacements = (
                self.legal_processor.standardize_terms(processed_text)
            )
            self._record_stage_completion(current_stage, stage_start_time)

            # Argument Extraction
            current_stage = PipelineStage.ARGUMENT_EXTRACTION
            stage_start_time = time.time()
            arguments = self.legal_processor.extract_arguments(standardized_text)
            self._record_stage_completion(current_stage, stage_start_time)

            # Timeline Construction
            current_stage = PipelineStage.TIMELINE_CONSTRUCTION
            stage_start_time = time.time()
            timeline = self.legal_processor.build_timeline(standardized_text)
            self._record_stage_completion(current_stage, stage_start_time)

            # Party Analysis
            current_stage = PipelineStage.PARTY_ANALYSIS
            stage_start_time = time.time()
            parties = self.legal_processor.extract_parties(standardized_text)
            self._record_stage_completion(current_stage, stage_start_time)

            # Update metadata with extracted information
            if metadata and isinstance(document, Document):
                document.extracted_citations = extracted_info.get('citations', [])
                document.legal_arguments = extracted_info.get('arguments', [])
                document.case_timeline = extracted_info.get('timeline', [])
                document.involved_parties = extracted_info.get('parties', {})

            # Stage: Storage
            self.stats.current_stage = PipelineStage.STORAGE
            chunk_ids, _ = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.document_processor.process_document,
                cleaned_text,
                metadata
            )

            # Track source if enabled
            if self.source_tracker and isinstance(document, Document):
                self.source_tracker.record_source(
                    doc_id=metadata.doc_id,
                    source_type=SourceType.COURT,
                    source_name=document.court_name or "unknown",
                    collector="system",
                    source_url=document.source_url
                )

            # Update stats
            self.stats.processed_documents += 1

            # Record successful processing
            processing_time = time.time() - start_time
            self.monitor.record_document_processed(True, processing_time)

            return metadata.doc_id

        except Exception as e:
            logger.error(f"Error in stage {current_stage}: {str(e)}")
            self.monitor.record_document_processed(False, time.time() - start_time)
            self.stats.failed_documents += 1
            if db and isinstance(document, Document):
                processing_record = ProcessingRecord(
                    document_id=document.id,
                    processing_type=current_stage,
                    status="failed",
                    error_message=str(e)
                )
                db.add(processing_record)
                db.commit()
            return None

    async def process_batch(
        self,
        documents: List[Union[str, Document]],
        db: Optional[Session] = None
    ) -> List[Optional[str]]:
        """Process a batch of documents.
        
        Args:
            documents: List of documents to process.
            db: Optional database session.
            
        Returns:
            List of document IDs for successfully processed documents.
        """
        self.stats.start_time = datetime.now()

        tasks = []
        for i in range(0, len(documents), self.config.batch_size):
            batch = documents[i:i + self.config.batch_size]
            batch_tasks = [
                self._process_document(doc, db=db)
                for doc in batch
            ]
            tasks.extend(batch_tasks)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        self.stats.end_time = datetime.now()
        return [r for r in results if isinstance(r, str)]

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics.
        
        Returns:
            Dictionary of pipeline statistics.
        """
        duration = None
        if self.stats.start_time and self.stats.end_time:
            duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        return {
            "total_documents": self.stats.total_documents,
            "processed_documents": self.stats.processed_documents,
            "failed_documents": self.stats.failed_documents,
            "success_rate": (
                self.stats.processed_documents / self.stats.total_documents
                if self.stats.total_documents > 0
                else 0
            ),
            "current_stage": self.stats.current_stage,
            "duration_seconds": duration,
            "start_time": self.stats.start_time,
            "end_time": self.stats.end_time
        }

    def reset_stats(self) -> None:
        """Reset pipeline statistics."""
        self.stats = PipelineStats()

    def _record_stage_completion(
        self,
        stage: PipelineStage,
        start_time: float,
        success: bool = True
    ) -> None:
        """Record stage completion metrics.
        
        Args:
            stage: Pipeline stage.
            start_time: Stage start time.
            success: Whether the stage completed successfully.
        """
        duration = time.time() - start_time
        self.monitor.record_pipeline_stage(stage, duration, success)

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics.
        
        Returns:
            Dictionary of pipeline statistics.
        """
        stats = self.get_stats()  # Get basic stats

        # Add performance stats
        performance_stats = self.monitor.get_performance_stats()
        stats.update({
            "performance": performance_stats,
            "error_rate": self.monitor.get_error_rate(),
            "recent_alerts": [
                alert.dict()
                for alert in self.monitor.get_recent_alerts(
                    since=datetime.now() - timedelta(minutes=30)
                )
            ]
        })

        return stats

    def cleanup(self) -> None:
        """Clean up pipeline resources."""
        self.executor.shutdown(wait=True)
        self.monitor.cleanup()
