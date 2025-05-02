"""Tests for document processor functionality."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from legal_doc_intelligence.processors.document_processor import DocumentMetadata, DocumentProcessor


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_metadata() -> DocumentMetadata:
    """Create sample document metadata."""
    return DocumentMetadata(
        doc_id="TEST-2024-001",
        case_type="民事",
        court="台北地方法院",
        date=datetime(2024, 1, 1),
        source="測試來源",
        title="測試案件"
    )

def test_document_processor_basic(temp_dir: Path, sample_metadata: DocumentMetadata) -> None:
    """Test basic document processing functionality."""
    processor = DocumentProcessor(persist_directory=temp_dir)

    # Test document text
    text = """
    台灣台北地方法院民事判決
    原告甲○○主張：被告乙○○未依約給付貨款新台幣50萬元。
    被告則抗辯：系爭貨物有瑕疵，依民法第359條主張同時履行抗辯。
    經查：兩造就系爭買賣契約之貨款支付條件約定為：驗收合格後30日內付款。
    被告雖抗辯貨物有瑕疵，然未能提出具體事證。
    故原告之請求，核無不合，應予准許。
    中華民國113年1月1日
    """

    # Process document
    chunk_ids = processor.process_document(text, sample_metadata)
    assert len(chunk_ids) > 0

    # Test search functionality
    results = processor.search_similar("貨款支付")
    assert len(results) > 0
    assert any("貨款" in result["document"] for result in results)

    # Test metadata preservation
    assert all(result["metadata"]["case_type"] == "民事" for result in results)
    assert all(result["metadata"]["court"] == "台北地方法院" for result in results)

def test_document_processor_text_splitting(temp_dir: Path, sample_metadata: DocumentMetadata) -> None:
    """Test text splitting functionality."""
    processor = DocumentProcessor(
        persist_directory=temp_dir,
        chunk_size=100,
        chunk_overlap=20
    )

    # Test document with multiple paragraphs
    text = "。".join([
        "第一段落內容" * 5,
        "第二段落內容" * 5,
        "第三段落內容" * 5
    ]) + "。"

    # Process document
    chunk_ids = processor.process_document(text, sample_metadata)

    # Should be split into multiple chunks due to size
    assert len(chunk_ids) > 1

    # Test chunk overlap
    results = processor.search_similar("第二段落")
    overlapping_chunks = sum(1 for r in results if "第二段落" in r["document"])
    assert overlapping_chunks >= 1

def test_document_processor_metadata_handling(temp_dir: Path, sample_metadata: DocumentMetadata) -> None:
    """Test metadata handling functionality."""
    processor = DocumentProcessor(persist_directory=temp_dir)

    text = "這是一個測試文件。" * 10

    # Process document
    chunk_ids = processor.process_document(text, sample_metadata)

    # Search and verify metadata
    results = processor.search_similar("測試文件")
    for result in results:
        metadata = result["metadata"]
        assert metadata["doc_id"] == sample_metadata.doc_id
        assert metadata["case_type"] == sample_metadata.case_type
        assert metadata["court"] == sample_metadata.court
        assert "chunk_index" in metadata
        assert "total_chunks" in metadata
        assert metadata["chunk_index"] < metadata["total_chunks"]

def test_document_processor_persistence(temp_dir: Path, sample_metadata: DocumentMetadata) -> None:
    """Test vector store persistence."""
    # Create and populate first processor
    processor1 = DocumentProcessor(persist_directory=temp_dir)
    text = "這是一個需要持久化儲存的測試文件。"
    processor1.process_document(text, sample_metadata)
    processor1.persist()

    # Create second processor with same directory
    processor2 = DocumentProcessor(persist_directory=temp_dir)

    # Search should work with second processor
    results = processor2.search_similar("持久化儲存")
    assert len(results) > 0
    assert any("持久化" in result["document"] for result in results)
