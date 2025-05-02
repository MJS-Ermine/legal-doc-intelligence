"""Document processor for legal text processing and vector storage."""

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jieba
from pydantic import BaseModel

from ..vectorstore.base import BaseVectorStore
from ..vectorstore.chroma import ChromaVectorStore
from .pii_processor import PIIMaskingConfig, PIIMatch, PIIProcessor
from .text_processor import TextProcessor

logger = logging.getLogger(__name__)

class DocumentVersion(BaseModel):
    """Document version information."""

    version_id: str
    timestamp: datetime
    hash: str
    changes: Optional[str] = None
    processor_version: str = "1.0.0"

class DocumentMetadata(BaseModel):
    """Metadata for legal documents."""

    doc_id: str
    case_type: str
    court: str
    date: datetime
    source: str
    title: str
    version: DocumentVersion
    pii_status: str = "unprocessed"  # unprocessed, masked, or encrypted

class DocumentProcessor:
    """文檔處理器，負責切分、清理、metadata、向量存儲整合。"""

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        persist_directory: Optional[Path] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        pii_config: Optional[PIIMaskingConfig] = None
    ):
        """Initialize the document processor.
        
        Args:
            vector_store: Vector store instance to use.
            persist_directory: Directory for vector store persistence.
            chunk_size: Maximum size of text chunks.
            chunk_overlap: Number of characters to overlap between chunks.
            pii_config: Configuration for PII masking.
        """
        self.vector_store = vector_store or ChromaVectorStore(
            persist_directory=persist_directory
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.pii_processor = PIIProcessor(masking_config=pii_config)
        self.text_processor = TextProcessor()

        # Version control storage
        self.version_dir = persist_directory / "versions" if persist_directory else None
        if self.version_dir:
            self.version_dir.mkdir(parents=True, exist_ok=True)

        # Load custom legal dictionary for jieba
        # 特許繁體中文註釋：載入自定義法律詞典
        self._load_legal_dictionary()

        logger.info(
            f"Initialized DocumentProcessor with chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def _load_legal_dictionary(self) -> None:
        """Load custom legal dictionary for jieba."""
        # TODO: 實作載入自定義法律詞典
        pass

    def _clean_text(self, text: str) -> str:
        """Clean the input text.
        
        Args:
            text: Input text to clean.
            
        Returns:
            Cleaned text.
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep Chinese punctuation
        text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s]', '', text)
        return text.strip()

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks.
        
        Args:
            text: Input text to split.
            
        Returns:
            List of text chunks.
        """
        # 特許繁體中文註釋：使用結巴分詞進行初步分句
        sentences = []
        for chunk in jieba.cut(text):
            # Split by common Chinese sentence endings
            parts = re.split(r'([。！？；])', chunk)
            for i in range(0, len(parts)-1, 2):
                if parts[i].strip():
                    sentences.append(parts[i] + (parts[i+1] if i+1 < len(parts) else ''))

        # Combine sentences into chunks with overlap
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Add current chunk to results
                chunks.append(''.join(current_chunk))
                # Keep last sentences for overlap
                overlap_size = 0
                overlap_chunk = []
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= self.chunk_overlap:
                        overlap_chunk.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break
                current_chunk = overlap_chunk
                current_length = overlap_size

            current_chunk.append(sentence)
            current_length += sentence_length

        if current_chunk:
            chunks.append(''.join(current_chunk))

        return chunks

    def _compute_hash(self, text: str) -> str:
        """Compute document hash.
        
        Args:
            text: Document text.
            
        Returns:
            Document hash.
        """
        return hashlib.sha256(text.encode()).hexdigest()

    def _save_version(
        self,
        doc_id: str,
        version: DocumentVersion,
        text: str
    ) -> None:
        """Save document version.
        
        Args:
            doc_id: Document ID.
            version: Version information.
            text: Document text.
        """
        if not self.version_dir:
            return

        version_path = self.version_dir / f"{doc_id}_{version.version_id}.json"
        version_data = {
            "metadata": version.model_dump(),
            "text": text
        }

        with open(version_path, "w", encoding="utf-8") as f:
            json.dump(version_data, f, ensure_ascii=False, default=str)

    def process_document(
        self,
        text: str,
        metadata: DocumentMetadata,
        mask_pii: bool = True
    ) -> Tuple[List[str], Optional[List[PIIMatch]]]:
        """Process a document and store it in the vector store.
        
        Args:
            text: Document text to process.
            metadata: Document metadata.
            mask_pii: Whether to mask PII information.
            
        Returns:
            Tuple of (chunk IDs, PII matches if any).
        """
        # Clean text
        cleaned_text = self._clean_text(text)

        # Handle PII
        pii_matches = None
        if mask_pii:
            masked_text, pii_matches = self.pii_processor.mask_pii(cleaned_text)
            cleaned_text = masked_text
            metadata.pii_status = "masked"

        # Compute document hash and create version
        doc_hash = self._compute_hash(cleaned_text)
        version = DocumentVersion(
            version_id=f"v{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            hash=doc_hash,
            changes="Initial version" if not hasattr(metadata, "version") else "Updated version"
        )
        metadata.version = version

        # Save version if enabled
        self._save_version(metadata.doc_id, version, cleaned_text)

        # Split into chunks
        chunks = self._split_text(cleaned_text)

        # Prepare metadata for each chunk
        chunk_metadatas = []
        for i, _ in enumerate(chunks):
            chunk_metadata = metadata.model_dump()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
            chunk_metadatas.append(chunk_metadata)

        # Store in vector store
        chunk_ids = self.vector_store.add_texts(
            texts=chunks,
            metadatas=chunk_metadatas
        )

        logger.info(
            f"Processed document {metadata.doc_id} into {len(chunks)} chunks"
        )
        return chunk_ids, pii_matches

    def search_similar(
        self,
        query: str,
        k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Search for similar text chunks.
        
        Args:
            query: Query text to search for.
            k: Number of results to return.
            filter_metadata: Optional metadata filters.
            **kwargs: Additional arguments passed to vector store.
            
        Returns:
            List of similar text chunks with metadata.
        """
        return self.vector_store.similarity_search(
            query,
            k=k,
            filter=filter_metadata,
            **kwargs
        )

    def get_document_versions(self, doc_id: str) -> List[DocumentVersion]:
        """Get all versions of a document.
        
        Args:
            doc_id: Document ID.
            
        Returns:
            List of document versions.
        """
        if not self.version_dir:
            return []

        versions = []
        for version_file in self.version_dir.glob(f"{doc_id}_*.json"):
            with open(version_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                versions.append(DocumentVersion(**data["metadata"]))

        return sorted(versions, key=lambda v: v.timestamp)

    def persist(self) -> None:
        """Persist the vector store if supported."""
        self.vector_store.persist()

    def process_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """處理單一文檔，清理文本、提取 metadata。

        Args:
            doc (Dict[str, Any]): 原始文檔資料
        Returns:
            Dict[str, Any]: 處理後文檔
        """
        text = doc.get("content", "")
        text = self.text_processor.clean_html(text)
        text = self.text_processor.remove_special_chars(text)
        text = self.text_processor.mask_personal_info(text)
        tokens = self.text_processor.tokenize(text)
        return {
            "id": doc.get("id"),
            "title": doc.get("title"),
            "content": text,
            "tokens": tokens,
            "metadata": doc.get("metadata", {}),
        }

    def split_document(self, text: str, max_length: int = 512) -> List[str]:
        """將長文本切分為多段。

        Args:
            text (str): 文本
            max_length (int): 每段最大長度
        Returns:
            List[str]: 切分後段落
        """
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]

    def save_to_vectorstore(self, docs: List[Dict[str, Any]]) -> None:
        """將文檔存入向量資料庫（預留接口）。

        Args:
            docs (List[Dict[str, Any]]): 文檔清單
        """
        # TODO: 整合 ChromaDB
        pass
