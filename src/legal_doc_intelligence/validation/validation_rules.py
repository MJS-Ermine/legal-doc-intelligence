"""Validation rules for legal document processing."""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import chardet
from pydantic import BaseModel


class ValidationLevel(str, Enum):
    """Validation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationResult(BaseModel):
    """Result of a validation check."""

    rule_name: str
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class DocumentStats:
    """Document statistics for validation."""

    size_bytes: int
    char_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    encoding: str

class LegalDocumentValidator:
    """Validator for legal documents with comprehensive rule checking."""

    def __init__(
        self,
        max_file_size_mb: float = 10.0,
        allowed_encodings: List[str] = None,
        required_fields: List[str] = None,
        min_word_count: int = 100,
        max_word_count: int = 100000
    ):
        """Initialize the validator.

        Args:
            max_file_size_mb: Maximum allowed file size in MB.
            allowed_encodings: List of allowed text encodings.
            required_fields: List of required metadata fields.
            min_word_count: Minimum word count for valid documents.
            max_word_count: Maximum word count for valid documents.
        """
        if required_fields is None:
            required_fields = ["case_number", "court", "date"]
        if allowed_encodings is None:
            allowed_encodings = ["utf-8", "ascii"]
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.allowed_encodings = allowed_encodings
        self.required_fields = required_fields
        self.min_word_count = min_word_count
        self.max_word_count = max_word_count

        # Compile regex patterns
        self.case_number_pattern = re.compile(r'\d{2,4}[\-年]\d{1,6}號?')
        self.date_pattern = re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}')

    def get_document_stats(self, content: str) -> DocumentStats:
        """Get document statistics.

        Args:
            content: Document content.

        Returns:
            Document statistics.
        """
        # Detect encoding
        encoding_result = chardet.detect(content.encode())

        # Calculate statistics
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        sentences = [s for p in paragraphs for s in p.split('.') if s.strip()]
        words = [w for s in sentences for w in s.split() if w.strip()]

        return DocumentStats(
            size_bytes=len(content.encode()),
            char_count=len(content),
            word_count=len(words),
            sentence_count=len(sentences),
            paragraph_count=len(paragraphs),
            encoding=encoding_result['encoding']
        )

    def validate_format(self, content: str) -> List[ValidationResult]:
        """Validate document format.

        Args:
            content: Document content.

        Returns:
            List of validation results.
        """
        results = []
        stats = self.get_document_stats(content)

        # Check file size
        if stats.size_bytes > self.max_file_size:
            results.append(
                ValidationResult(
                    rule_name="file_size",
                    level=ValidationLevel.ERROR,
                    message=f"File size exceeds maximum allowed ({self.max_file_size} bytes)",
                    details={"size": stats.size_bytes}
                )
            )

        # Check encoding
        if stats.encoding not in self.allowed_encodings:
            results.append(
                ValidationResult(
                    rule_name="encoding",
                    level=ValidationLevel.ERROR,
                    message=f"Invalid encoding: {stats.encoding}",
                    details={"encoding": stats.encoding}
                )
            )

        # Check word count
        if stats.word_count < self.min_word_count:
            results.append(
                ValidationResult(
                    rule_name="min_word_count",
                    level=ValidationLevel.ERROR,
                    message=f"Document too short ({stats.word_count} words)",
                    details={"word_count": stats.word_count}
                )
            )
        elif stats.word_count > self.max_word_count:
            results.append(
                ValidationResult(
                    rule_name="max_word_count",
                    level=ValidationLevel.ERROR,
                    message=f"Document too long ({stats.word_count} words)",
                    details={"word_count": stats.word_count}
                )
            )

        return results

    def validate_content(self, content: str) -> List[ValidationResult]:
        """Validate document content.

        Args:
            content: Document content.

        Returns:
            List of validation results.
        """
        results = []

        # Check for case number
        if not self.case_number_pattern.search(content):
            results.append(
                ValidationResult(
                    rule_name="case_number_format",
                    level=ValidationLevel.WARNING,
                    message="Case number not found or invalid format"
                )
            )

        # Check for date
        if not self.date_pattern.search(content):
            results.append(
                ValidationResult(
                    rule_name="date_format",
                    level=ValidationLevel.WARNING,
                    message="Date not found or invalid format"
                )
            )

        # Check document structure
        if not content.strip().startswith(('判決書', '裁定書', '決定書')):
            results.append(
                ValidationResult(
                    rule_name="document_header",
                    level=ValidationLevel.WARNING,
                    message="Document does not start with expected legal document header"
                )
            )

        return results

    def validate_metadata(
        self,
        metadata: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate document metadata.

        Args:
            metadata: Document metadata.

        Returns:
            List of validation results.
        """
        results = []

        # Check required fields
        for field in self.required_fields:
            if field not in metadata or not metadata[field]:
                results.append(
                    ValidationResult(
                        rule_name="required_field",
                        level=ValidationLevel.ERROR,
                        message=f"Missing required field: {field}",
                        field=field
                    )
                )

        # Validate date format and range
        if 'date' in metadata:
            try:
                date = datetime.fromisoformat(str(metadata['date']))
                if date > datetime.now():
                    results.append(
                        ValidationResult(
                            rule_name="future_date",
                            level=ValidationLevel.ERROR,
                            message="Document date is in the future",
                            field="date"
                        )
                    )
            except (ValueError, TypeError):
                results.append(
                    ValidationResult(
                        rule_name="invalid_date",
                        level=ValidationLevel.ERROR,
                        message="Invalid date format",
                        field="date"
                    )
                )

        return results

    def validate(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate document content and metadata.

        Args:
            content: Document content.
            metadata: Document metadata.

        Returns:
            List of validation results.
        """
        results = []
        results.extend(self.validate_format(content))
        results.extend(self.validate_content(content))
        results.extend(self.validate_metadata(metadata))
        return results
