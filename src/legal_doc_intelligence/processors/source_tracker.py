"""Source tracking module for legal documents."""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)

class SourceType(str, Enum):
    """Types of document sources."""

    COURT_WEBSITE = "court_website"  # 法院網站
    OFFICIAL_GAZETTE = "official_gazette"  # 公報
    MANUAL_INPUT = "manual_input"  # 手動輸入
    API = "api"  # API 來源
    UNKNOWN = "unknown"  # 未知來源

class SourceMetadata(BaseModel):
    """Metadata for document sources."""

    source_type: SourceType
    source_url: Optional[HttpUrl] = None
    source_name: str
    collection_time: datetime
    collector: str
    verification_status: str = "unverified"  # unverified, verified, or rejected
    verification_method: Optional[str] = None
    verification_time: Optional[datetime] = None
    verification_by: Optional[str] = None
    additional_info: Dict[str, Any] = Field(default_factory=dict)

class SourceVerificationResult(BaseModel):
    """Result of source verification."""

    is_verified: bool
    verification_method: str
    verification_time: datetime
    verification_by: str
    notes: Optional[str] = None

class SourceTracker:
    """Tracker for document sources."""

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        auto_verify: bool = False
    ):
        """Initialize the source tracker.

        Args:
            storage_dir: Directory for storing source records.
            auto_verify: Whether to automatically verify sources when possible.
        """
        self.storage_dir = storage_dir
        if storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.auto_verify = auto_verify

        logger.info(f"Initialized SourceTracker with auto_verify={auto_verify}")

    def _save_source_record(
        self,
        doc_id: str,
        metadata: SourceMetadata
    ) -> None:
        """Save source record to storage.

        Args:
            doc_id: Document ID.
            metadata: Source metadata.
        """
        if not self.storage_dir:
            return

        record_path = self.storage_dir / f"{doc_id}_source.json"
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(metadata.model_dump(), f, ensure_ascii=False, default=str)

    def _load_source_record(self, doc_id: str) -> Optional[SourceMetadata]:
        """Load source record from storage.

        Args:
            doc_id: Document ID.

        Returns:
            Source metadata if found.
        """
        if not self.storage_dir:
            return None

        record_path = self.storage_dir / f"{doc_id}_source.json"
        if not record_path.exists():
            return None

        with open(record_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return SourceMetadata(**data)

    def record_source(
        self,
        doc_id: str,
        source_type: SourceType,
        source_name: str,
        collector: str,
        source_url: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> SourceMetadata:
        """Record document source information.

        Args:
            doc_id: Document ID.
            source_type: Type of source.
            source_name: Name of source.
            collector: Name of person/system collecting the document.
            source_url: Optional URL of source.
            additional_info: Optional additional information.

        Returns:
            Created source metadata.
        """
        metadata = SourceMetadata(
            source_type=source_type,
            source_name=source_name,
            source_url=source_url,
            collection_time=datetime.now(),
            collector=collector,
            additional_info=additional_info or {}
        )

        # Auto-verify if enabled
        if self.auto_verify and source_url:
            self.verify_source(doc_id, metadata)

        self._save_source_record(doc_id, metadata)

        logger.info(
            f"Recorded source for document {doc_id} "
            f"from {source_name} ({source_type})"
        )
        return metadata

    def verify_source(
        self,
        doc_id: str,
        metadata: Optional[SourceMetadata] = None,
        verification_method: str = "manual",
        verifier: str = "system",
        notes: Optional[str] = None
    ) -> SourceVerificationResult:
        """Verify document source.

        Args:
            doc_id: Document ID.
            metadata: Source metadata to verify. If None, loads from storage.
            verification_method: Method used for verification.
            verifier: Name of person/system performing verification.
            notes: Optional verification notes.

        Returns:
            Verification result.
        """
        if metadata is None:
            metadata = self._load_source_record(doc_id)
            if metadata is None:
                raise ValueError(f"No source record found for document {doc_id}")

        # Perform verification
        is_verified = True  # 實際應用中應該根據不同的驗證方法進行驗證

        # Update metadata
        metadata.verification_status = "verified" if is_verified else "rejected"
        metadata.verification_method = verification_method
        metadata.verification_time = datetime.now()
        metadata.verification_by = verifier

        # Save updated record
        self._save_source_record(doc_id, metadata)

        result = SourceVerificationResult(
            is_verified=is_verified,
            verification_method=verification_method,
            verification_time=metadata.verification_time,
            verification_by=verifier,
            notes=notes
        )

        logger.info(
            f"Verified source for document {doc_id}: "
            f"{'verified' if is_verified else 'rejected'}"
        )
        return result

    def get_source_info(self, doc_id: str) -> Optional[SourceMetadata]:
        """Get source information for a document.

        Args:
            doc_id: Document ID.

        Returns:
            Source metadata if found.
        """
        return self._load_source_record(doc_id)

    def list_sources_by_type(
        self,
        source_type: SourceType
    ) -> List[SourceMetadata]:
        """List all sources of a specific type.

        Args:
            source_type: Type of source to list.

        Returns:
            List of source metadata.
        """
        if not self.storage_dir:
            return []

        sources = []
        for record_file in self.storage_dir.glob("*_source.json"):
            with open(record_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                metadata = SourceMetadata(**data)
                if metadata.source_type == source_type:
                    sources.append(metadata)

        return sources
