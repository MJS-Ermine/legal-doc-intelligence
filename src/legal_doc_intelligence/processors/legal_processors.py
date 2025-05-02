"""Legal-specific document processing stages."""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..validation.validation_rules import ValidationLevel, ValidationResult


@dataclass
class Citation:
    """Legal citation information."""

    case_number: str
    court: str
    date: Optional[datetime] = None
    text: str = ""
    start_pos: int = 0
    end_pos: int = 0

@dataclass
class LegalTerm:
    """Standardized legal term."""

    original: str
    standard: str
    category: str
    confidence: float

@dataclass
class Argument:
    """Legal argument structure."""

    text: str
    type: str  # e.g., "claim", "evidence", "reasoning"
    strength: float  # 0.0 to 1.0
    supporting_citations: List[Citation]

@dataclass
class Timeline:
    """Case timeline entry."""

    date: datetime
    event: str
    importance: float  # 0.0 to 1.0
    related_parties: List[str]

@dataclass
class Party:
    """Case party information."""

    name: str
    role: str
    relationships: Dict[str, str]  # party_name -> relationship_type

class LegalProcessor:
    """Processor for legal-specific document analysis."""

    def __init__(self):
        """Initialize the processor."""
        # Load legal term dictionary
        self.legal_terms = self._load_legal_terms()

        # Compile regex patterns
        self.citation_pattern = re.compile(
            r'(?P<court>[^，。；]+)(?P<year>\d{2,4})年度?第?(?P<number>\d+)號'
        )

        # Initialize relationship patterns
        self.relationship_patterns = {
            "原告": r"原告[：\s]*([^，。；]+)",
            "被告": r"被告[：\s]*([^，。；]+)",
            "上訴人": r"上訴人[：\s]*([^，。；]+)",
            "被上訴人": r"被上訴人[：\s]*([^，。；]+)"
        }

    def _load_legal_terms(self) -> Dict[str, str]:
        """Load standardized legal terms dictionary.
        
        Returns:
            Dictionary mapping original terms to standard forms.
        """
        # TODO: Load from external source
        return {
            "給付": "支付",
            "請求": "要求",
            "陳稱": "表示",
            "系爭": "爭議",
            "兩造": "雙方"
        }

    def extract_citations(self, text: str) -> List[Citation]:
        """Extract legal citations from text.
        
        Args:
            text: Document text.
            
        Returns:
            List of extracted citations.
        """
        citations = []
        for match in self.citation_pattern.finditer(text):
            start = match.start()
            end = match.end()

            # Extract context (up to 100 chars before and after)
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            citation_text = text[context_start:context_end]

            citations.append(Citation(
                case_number=f"{match['year']}年{match['number']}號",
                court=match['court'],
                text=citation_text,
                start_pos=start,
                end_pos=end
            ))

        return citations

    def standardize_terms(self, text: str) -> Tuple[str, List[LegalTerm]]:
        """Standardize legal terms in text.
        
        Args:
            text: Document text.
            
        Returns:
            Tuple of (standardized text, list of term replacements).
        """
        replacements = []
        standardized = text

        for original, standard in self.legal_terms.items():
            if original in text:
                standardized = standardized.replace(original, standard)
                replacements.append(LegalTerm(
                    original=original,
                    standard=standard,
                    category="general",
                    confidence=1.0
                ))

        return standardized, replacements

    def extract_arguments(self, text: str) -> List[Argument]:
        """Extract legal arguments from text.
        
        Args:
            text: Document text.
            
        Returns:
            List of extracted arguments.
        """
        arguments = []

        # Simple pattern matching for now
        # TODO: Implement more sophisticated argument mining
        claim_patterns = [
            r"主張[：\s]*([^。]+)",
            r"請求[：\s]*([^。]+)",
            r"抗辯[：\s]*([^。]+)"
        ]

        for pattern in claim_patterns:
            for match in re.finditer(pattern, text):
                # Extract citations in the argument
                arg_text = match.group(1)
                citations = self.extract_citations(arg_text)

                arguments.append(Argument(
                    text=arg_text,
                    type="claim",
                    strength=0.8 if citations else 0.5,
                    supporting_citations=citations
                ))

        return arguments

    def build_timeline(self, text: str) -> List[Timeline]:
        """Build case timeline from text.
        
        Args:
            text: Document text.
            
        Returns:
            List of timeline entries.
        """
        timeline = []
        date_pattern = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日([^。]+)')

        for match in date_pattern.finditer(text):
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            event = match.group(4).strip()

            # Extract related parties
            parties = []
            for role, pattern in self.relationship_patterns.items():
                party_matches = re.findall(pattern, event)
                parties.extend(party_matches)

            timeline.append(Timeline(
                date=datetime(year, month, day),
                event=event,
                importance=0.7 if parties else 0.5,
                related_parties=parties
            ))

        return sorted(timeline, key=lambda x: x.date)

    def extract_parties(self, text: str) -> Dict[str, Party]:
        """Extract case parties and their relationships.
        
        Args:
            text: Document text.
            
        Returns:
            Dictionary mapping party names to Party objects.
        """
        parties = {}
        relationships = defaultdict(dict)

        # Extract parties by role
        for role, pattern in self.relationship_patterns.items():
            matches = re.findall(pattern, text)
            for name in matches:
                if name not in parties:
                    parties[name] = Party(
                        name=name,
                        role=role,
                        relationships={}
                    )

        # Analyze relationships
        for name1 in parties:
            for name2 in parties:
                if name1 != name2:
                    # Check if they appear in the same sentence
                    for sentence in text.split('。'):
                        if name1 in sentence and name2 in sentence:
                            relationship = "關聯方"  # Default relationship
                            if "共同" in sentence:
                                relationship = "共同當事人"
                            elif "訴訟代理人" in sentence:
                                relationship = "代理關係"

                            relationships[name1][name2] = relationship
                            relationships[name2][name1] = relationship

        # Update party relationships
        for name, party in parties.items():
            party.relationships = relationships[name]

        return parties

    def process_document(
        self,
        text: str
    ) -> Tuple[str, Dict[str, Any], List[ValidationResult]]:
        """Process legal document with all available processors.
        
        Args:
            text: Document text.
            
        Returns:
            Tuple of (processed text, extracted information, validation results).
        """
        validation_results = []
        extracted_info = {}

        try:
            # Standardize terms
            processed_text, term_replacements = self.standardize_terms(text)
            extracted_info['standardized_terms'] = term_replacements

            # Extract citations
            citations = self.extract_citations(processed_text)
            extracted_info['citations'] = citations

            if not citations:
                validation_results.append(ValidationResult(
                    rule_name="citations",
                    level=ValidationLevel.WARNING,
                    message="No legal citations found in document"
                ))

            # Extract arguments
            arguments = self.extract_arguments(processed_text)
            extracted_info['arguments'] = arguments

            if not arguments:
                validation_results.append(ValidationResult(
                    rule_name="arguments",
                    level=ValidationLevel.WARNING,
                    message="No clear legal arguments identified"
                ))

            # Build timeline
            timeline = self.build_timeline(processed_text)
            extracted_info['timeline'] = timeline

            # Extract parties
            parties = self.extract_parties(processed_text)
            extracted_info['parties'] = parties

            if not parties:
                validation_results.append(ValidationResult(
                    rule_name="parties",
                    level=ValidationLevel.ERROR,
                    message="No case parties identified"
                ))

        except Exception as e:
            validation_results.append(ValidationResult(
                rule_name="processing_error",
                level=ValidationLevel.ERROR,
                message=f"Error during legal processing: {str(e)}"
            ))

        return processed_text, extracted_info, validation_results
