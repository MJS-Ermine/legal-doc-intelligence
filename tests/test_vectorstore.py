"""Tests for vector store functionality."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from legal_doc_intelligence.vectorstore.chroma import ChromaVectorStore


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

def test_chroma_vector_store_basic(temp_dir: Path) -> None:
    """Test basic vector store operations."""
    # Initialize store
    store = ChromaVectorStore(
        collection_name="test_collection",
        persist_directory=temp_dir
    )

    # Test documents
    docs = [
        "這是一個關於合約糾紛的案件",
        "這個案件涉及商標侵權",
        "這是一個刑事案件的判決",
        "這個案件討論著作權問題"
    ]

    # Add documents
    ids = store.add_texts(docs)
    assert len(ids) == 4

    # Test similarity search
    results = store.similarity_search("商標侵權", k=2)
    assert len(results) == 2
    assert any("商標" in result["document"] for result in results)

    # Test persistence
    store.persist()

    # Create new store instance and verify data
    new_store = ChromaVectorStore(
        collection_name="test_collection",
        persist_directory=temp_dir
    )
    new_store.load()

    results = new_store.similarity_search("著作權", k=1)
    assert len(results) == 1
    assert "著作權" in results[0]["document"]

def test_chroma_vector_store_metadata(temp_dir: Path) -> None:
    """Test vector store operations with metadata."""
    store = ChromaVectorStore(
        collection_name="test_collection",
        persist_directory=temp_dir
    )

    # Test documents with metadata
    docs = [
        "原告主張被告違反合約約定",
        "被告否認違約事實"
    ]

    metadatas = [
        {"case_type": "民事", "year": 2023, "court": "台北地方法院"},
        {"case_type": "民事", "year": 2023, "court": "台北地方法院"}
    ]

    # Add documents with metadata
    ids = store.add_texts(docs, metadatas=metadatas)
    assert len(ids) == 2

    # Test search with metadata
    results = store.similarity_search("違約")
    assert len(results) > 0
    assert all(result["metadata"]["case_type"] == "民事" for result in results)
    assert all(result["metadata"]["year"] == 2023 for result in results)

def test_add_and_query_documents(tmp_path):
    store = ChromaVectorStore(persist_directory=str(tmp_path))
    docs = [
        {"id": 1, "content": "台灣高等法院判決書", "metadata": {"court": "高等法院"}},
        {"id": 2, "content": "最高法院裁定", "metadata": {"court": "最高法院"}},
    ]
    store.add_documents(docs)
    results = store.query("高等法院", top_k=1)
    assert len(results) == 1
    assert "高等法院" in results[0]
    store.persist()
