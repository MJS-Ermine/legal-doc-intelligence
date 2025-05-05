"""Query optimization module for legal document retrieval."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import jieba
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class QueryExpansion(BaseModel):
    """Query expansion configuration."""

    original_terms: List[str]
    synonyms: Dict[str, List[str]]
    legal_terms: Dict[str, List[str]]
    weights: Dict[str, float] = Field(default_factory=lambda: {
        "original": 1.0,
        "synonym": 0.7,
        "legal": 0.8
    })

class QueryOptimizer:
    """Query optimizer for legal document retrieval.

    Features:
    1. Query segmentation and normalization
    2. Legal term expansion
    3. Synonym expansion
    4. Query rewriting
    """

    def __init__(
        self,
        legal_terms_path: Optional[Path] = None,
        synonyms_path: Optional[Path] = None
    ):
        """Initialize the query optimizer.

        Args:
            legal_terms_path: Path to legal terms dictionary.
            synonyms_path: Path to synonyms dictionary.
        """
        self.legal_terms = self._load_dict(legal_terms_path) if legal_terms_path else {}
        self.synonyms = self._load_dict(synonyms_path) if synonyms_path else {}

        # 特許繁體中文註釋：載入自定義詞典
        self._load_custom_dict()

        logger.info("Initialized QueryOptimizer")

    def _load_dict(self, path: Path) -> Dict[str, List[str]]:
        """Load dictionary from JSON file.

        Args:
            path: Path to dictionary file.

        Returns:
            Dictionary mapping terms to related terms.
        """
        if not path.exists():
            return {}

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_custom_dict(self) -> None:
        """Load custom dictionary for jieba."""
        # TODO: 實作載入自定義詞典
        pass

    def _normalize_query(self, query: str) -> str:
        """Normalize query text.

        Args:
            query: Original query text.

        Returns:
            Normalized query text.
        """
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query)
        # Normalize punctuation
        query = re.sub(r'[，。！？；]', ',', query)
        return query.strip().lower()

    def _segment_query(self, query: str) -> List[str]:
        """Segment query into terms.

        Args:
            query: Query text.

        Returns:
            List of query terms.
        """
        return [term for term in jieba.cut(query) if term.strip()]

    def expand_query(self, query: str) -> QueryExpansion:
        """Expand query with synonyms and legal terms.

        Args:
            query: Original query text.

        Returns:
            Query expansion result.
        """
        # Normalize and segment query
        normalized = self._normalize_query(query)
        terms = self._segment_query(normalized)

        # Collect expansions
        synonyms: Dict[str, List[str]] = {}
        legal_terms: Dict[str, List[str]] = {}

        for term in terms:
            # Add synonyms
            if term in self.synonyms:
                synonyms[term] = self.synonyms[term]

            # Add legal terms
            if term in self.legal_terms:
                legal_terms[term] = self.legal_terms[term]

        return QueryExpansion(
            original_terms=terms,
            synonyms=synonyms,
            legal_terms=legal_terms
        )

    def rewrite_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Rewrite query based on expansion and context.

        Args:
            query: Original query text.
            context: Optional query context.

        Returns:
            List of rewritten queries.
        """
        expansion = self.expand_query(query)
        rewrites = [query]  # Start with original query

        # Add expansions
        for term in expansion.original_terms:
            # Add synonym expansions
            if term in expansion.synonyms:
                for synonym in expansion.synonyms[term]:
                    new_query = query.replace(term, synonym)
                    rewrites.append(new_query)

            # Add legal term expansions
            if term in expansion.legal_terms:
                for legal_term in expansion.legal_terms[term]:
                    new_query = query.replace(term, legal_term)
                    rewrites.append(new_query)

        # Consider context if available
        if context:
            # Add context-specific rewrites
            if 'case_type' in context:
                rewrites.extend([
                    f"{context['case_type']} {q}"
                    for q in rewrites
                ])

            if 'court_level' in context:
                rewrites.extend([
                    f"{context['court_level']} {q}"
                    for q in rewrites
                ])

        return list(set(rewrites))  # Remove duplicates

class MultiStageRetriever:
    """Multi-stage retriever for legal documents.

    Features:
    1. Query optimization
    2. Multi-stage retrieval
    3. Result fusion
    4. Context-aware ranking
    """

    def __init__(
        self,
        query_optimizer: QueryOptimizer,
        vector_store: Any,  # Will be EnhancedChromaStore
        initial_k: int = 10,
        final_k: int = 4
    ):
        """Initialize the multi-stage retriever.

        Args:
            query_optimizer: Query optimizer instance.
            vector_store: Vector store instance.
            initial_k: Number of results for initial retrieval.
            final_k: Number of results for final output.
        """
        self.query_optimizer = query_optimizer
        self.vector_store = vector_store
        self.initial_k = initial_k
        self.final_k = final_k

        logger.info(
            f"Initialized MultiStageRetriever with "
            f"initial_k={initial_k}, final_k={final_k}"
        )

    def _merge_results(
        self,
        results_list: List[List[Dict[str, Any]]],
        weights: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Merge multiple result lists with optional weights.

        Args:
            results_list: List of result lists to merge.
            weights: Optional weights for each result list.

        Returns:
            Merged and deduplicated results.
        """
        if weights is None:
            weights = [1.0] * len(results_list)

        # Collect all results with scores
        scored_results: Dict[str, Dict[str, Any]] = {}

        for results, weight in zip(results_list, weights, strict=False):
            for result in results:
                doc_id = result['id']
                score = result.get('final_score', 0.0) * weight

                if doc_id not in scored_results:
                    scored_results[doc_id] = result.copy()
                    scored_results[doc_id]['final_score'] = score
                else:
                    # Update score if higher
                    if score > scored_results[doc_id]['final_score']:
                        scored_results[doc_id] = result.copy()
                        scored_results[doc_id]['final_score'] = score

        # Sort by final score
        merged = list(scored_results.values())
        merged.sort(key=lambda x: x['final_score'], reverse=True)
        return merged

    def retrieve(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Perform multi-stage retrieval.

        Args:
            query: Query text.
            context: Optional query context.
            **kwargs: Additional arguments passed to vector store.

        Returns:
            List of retrieved documents.
        """
        # Generate query rewrites
        rewrites = self.query_optimizer.rewrite_query(query, context)

        # Perform initial retrieval for each rewrite
        all_results = []
        weights = []

        for i, rewrite in enumerate(rewrites):
            # Original query gets highest weight
            weight = 1.0 if i == 0 else 0.7

            results = self.vector_store.similarity_search(
                query=rewrite,
                k=self.initial_k,
                **kwargs
            )

            all_results.append(results)
            weights.append(weight)

        # Merge and rerank results
        merged_results = self._merge_results(all_results, weights)

        # Return top k results
        return merged_results[:self.final_k]
