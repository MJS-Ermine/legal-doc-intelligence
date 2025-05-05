"""PII (Personal Identifiable Information) processor for legal documents."""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Pattern

import spacy
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PIIType(str, Enum):
    """Types of PII information."""

    ID_NUMBER = "id_number"  # 身份證字號
    NAME = "name"  # 姓名
    ADDRESS = "address"  # 地址
    PHONE = "phone"  # 電話號碼
    EMAIL = "email"  # 電子郵件
    BANK_ACCOUNT = "bank_account"  # 銀行帳號
    CUSTOM = "custom"  # 自定義

class PIIMatch(BaseModel):
    """Model for PII matches."""

    type: PIIType
    value: str
    start: int
    end: int
    masked_value: str

class PIIMaskingConfig(BaseModel):
    """Configuration for PII masking."""

    mask_char: str = "*"
    id_number_format: str = "****{last4}"
    name_format: str = "{first}**"
    address_format: str = "{first3}****"
    phone_format: str = "****{last4}"
    email_format: str = "{username_first3}***@{domain}"
    custom_format: Optional[str] = None

class PIIProcessor:
    """Processor for handling PII in legal documents."""

    def __init__(
        self,
        masking_config: Optional[PIIMaskingConfig] = None,
        custom_patterns: Optional[Dict[str, Pattern]] = None,
        load_spacy_model: bool = True
    ):
        """Initialize the PII processor.

        Args:
            masking_config: Configuration for PII masking.
            custom_patterns: Custom regex patterns for PII detection.
            load_spacy_model: Whether to load the spaCy model for NER.
        """
        self.config = masking_config or PIIMaskingConfig()
        self.custom_patterns = custom_patterns or {}

        # 特許繁體中文註釋：載入繁體中文 NER 模型
        self.nlp = None
        if load_spacy_model:
            try:
                self.nlp = spacy.load("zh_core_web_sm")
                logger.info("Loaded spaCy model for Chinese NER")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model: {e}")

        # Compile regex patterns
        self._compile_patterns()

        logger.info("Initialized PIIProcessor")

    def _compile_patterns(self) -> None:
        """Compile regex patterns for PII detection."""
        self.patterns = {
            PIIType.ID_NUMBER: re.compile(
                r'[A-Z][12]\d{8}'  # 台灣身份證字號格式
            ),
            PIIType.PHONE: re.compile(
                r'(?:09\d{8}|0[2-8]-?\d{6,8})'  # 手機號碼和市話格式
            ),
            PIIType.EMAIL: re.compile(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ),
            PIIType.BANK_ACCOUNT: re.compile(
                r'\d{10,16}'  # 銀行帳號一般格式
            )
        }
        self.patterns.update(self.custom_patterns)

    def _mask_value(self, pii_type: PIIType, value: str) -> str:
        """Mask PII value according to configuration.

        Args:
            pii_type: Type of PII.
            value: Original value to mask.

        Returns:
            Masked value.
        """
        if pii_type == PIIType.ID_NUMBER:
            return self.config.id_number_format.format(
                last4=value[-4:]
            ).replace("{", self.config.mask_char)
        elif pii_type == PIIType.NAME:
            return self.config.name_format.format(
                first=value[0]
            ).replace("{", self.config.mask_char)
        elif pii_type == PIIType.ADDRESS:
            return self.config.address_format.format(
                first3=value[:3]
            ).replace("{", self.config.mask_char)
        elif pii_type == PIIType.PHONE:
            return self.config.phone_format.format(
                last4=value[-4:]
            ).replace("{", self.config.mask_char)
        elif pii_type == PIIType.EMAIL:
            username, domain = value.split("@")
            return self.config.email_format.format(
                username_first3=username[:3],
                domain=domain
            ).replace("{", self.config.mask_char)
        else:
            return self.config.mask_char * len(value)

    def detect_pii(self, text: str) -> List[PIIMatch]:
        """Detect PII in text.

        Args:
            text: Input text to process.

        Returns:
            List of PII matches.
        """
        matches: List[PIIMatch] = []

        # Regex-based detection
        for pii_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                matches.append(
                    PIIMatch(
                        type=pii_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        masked_value=self._mask_value(pii_type, match.group())
                    )
                )

        # NER-based detection for names and addresses
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "GPE", "LOC"]:
                    pii_type = PIIType.NAME if ent.label_ == "PERSON" else PIIType.ADDRESS
                    matches.append(
                        PIIMatch(
                            type=pii_type,
                            value=ent.text,
                            start=ent.start_char,
                            end=ent.end_char,
                            masked_value=self._mask_value(pii_type, ent.text)
                        )
                    )

        return sorted(matches, key=lambda x: x.start)

    def mask_pii(self, text: str) -> tuple[str, List[PIIMatch]]:
        """Mask PII in text.

        Args:
            text: Input text to process.

        Returns:
            Tuple of (masked text, list of PII matches).
        """
        matches = self.detect_pii(text)
        result = list(text)

        # Replace PII with masked values
        for match in reversed(matches):  # Process from end to avoid offset issues
            result[match.start:match.end] = match.masked_value

        return ''.join(result), matches

    def add_custom_pattern(
        self,
        name: str,
        pattern: str,
        mask_format: Optional[str] = None
    ) -> None:
        """Add custom pattern for PII detection.

        Args:
            name: Name for the pattern.
            pattern: Regex pattern string.
            mask_format: Optional custom mask format.
        """
        self.patterns[PIIType.CUSTOM] = re.compile(pattern)
        if mask_format:
            self.config.custom_format = mask_format
