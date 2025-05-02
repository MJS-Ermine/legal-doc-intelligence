"""Tests for RAG functionality."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from legal_doc_intelligence.processors.document_processor import DocumentMetadata, DocumentProcessor
from legal_doc_intelligence.rag.legal_rag import LegalRAG


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

@pytest.fixture
def document_processor(temp_dir: Path) -> DocumentProcessor:
    """Create a document processor instance."""
    return DocumentProcessor(persist_directory=temp_dir)

@pytest.fixture
def rag_system(document_processor: DocumentProcessor) -> LegalRAG:
    """Create a RAG system instance."""
    with patch("langchain.chat_models.ChatOpenAI") as mock_llm:
        # Mock LLM responses
        mock_llm.return_value = MagicMock()
        mock_llm.return_value.predict.return_value = "模擬的 LLM 回應"

        return LegalRAG(
            document_processor=document_processor,
            model_name="gpt-3.5-turbo",
            streaming=False
        )

def test_rag_qa(
    rag_system: LegalRAG,
    document_processor: DocumentProcessor,
    sample_metadata: DocumentMetadata
) -> None:
    """Test RAG question answering functionality."""
    # Add test documents
    text = """
    台灣台北地方法院民事判決
    原告甲○○主張：被告乙○○未依約給付貨款新台幣50萬元。
    被告則抗辯：系爭貨物有瑕疵，依民法第359條主張同時履行抗辯。
    經查：兩造就系爭買賣契約之貨款支付條件約定為：驗收合格後30日內付款。
    被告雖抗辯貨物有瑕疵，然未能提出具體事證。
    故原告之請求，核無不合，應予准許。
    中華民國113年1月1日
    """
    document_processor.process_document(text, sample_metadata)

    # Test QA
    response, documents = rag_system.query("被告的抗辯理由是什麼？")

    assert response == "模擬的 LLM 回應"
    assert len(documents) > 0
    assert any("同時履行抗辯" in doc.page_content for doc in documents)

def test_rag_summary(
    rag_system: LegalRAG,
    document_processor: DocumentProcessor,
    sample_metadata: DocumentMetadata
) -> None:
    """Test RAG summarization functionality."""
    # Add test documents
    text = """
    台灣台北地方法院民事判決
    原告甲○○主張：被告乙○○未依約給付貨款新台幣50萬元。
    被告則抗辯：系爭貨物有瑕疵，依民法第359條主張同時履行抗辯。
    經查：兩造就系爭買賣契約之貨款支付條件約定為：驗收合格後30日內付款。
    被告雖抗辯貨物有瑕疵，然未能提出具體事證。
    故原告之請求，核無不合，應予准許。
    中華民國113年1月1日
    """
    document_processor.process_document(text, sample_metadata)

    # Test summarization
    summary, documents = rag_system.summarize("貨款給付")

    assert summary == "模擬的 LLM 回應"
    assert len(documents) > 0
    assert any("貨款" in doc.page_content for doc in documents)

def test_rag_no_results(
    rag_system: LegalRAG,
    document_processor: DocumentProcessor
) -> None:
    """Test RAG behavior when no relevant documents are found."""
    # Test with empty vector store
    response, documents = rag_system.query("這是一個不存在的案件")

    assert "抱歉" in response.lower()
    assert len(documents) == 0

def test_rag_retrieval_filtering(
    rag_system: LegalRAG,
    document_processor: DocumentProcessor,
    sample_metadata: DocumentMetadata
) -> None:
    """Test RAG retrieval with filtering."""
    # Add test documents
    texts = [
        "這是一個民事案件關於貨款給付",
        "這是一個刑事案件關於詐欺",
        "這是另一個民事案件關於損害賠償"
    ]

    for i, text in enumerate(texts):
        metadata = sample_metadata.model_copy()
        metadata.doc_id = f"TEST-2024-{i+1:03d}"
        metadata.case_type = "民事" if "民事" in text else "刑事"
        document_processor.process_document(text, metadata)

    # Test retrieval with filtering
    documents = rag_system.retrieve(
        query="案件",
        filters={"metadata.case_type": "民事"}
    )

    assert len(documents) > 0
    assert all(
        doc.metadata.get("case_type") == "民事"
        for doc in documents
    )
