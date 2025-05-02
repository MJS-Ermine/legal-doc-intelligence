"""
測試文件處理模組的功能
"""
from pathlib import Path

import pytest

from legal_doc_intelligence.document import Document
from legal_doc_intelligence.exceptions import DocumentError


@pytest.fixture
def sample_file_path() -> str:
    """獲取示例文件路徑"""
    return "examples/case1.txt"

@pytest.fixture
def sample_contract_path() -> str:
    """獲取示例合約文件路徑"""
    return "examples/contract1.txt"

def test_document_creation(sample_file_path: str):
    """測試文件對象創建"""
    doc = Document.from_file(sample_file_path)

    assert doc is not None
    assert isinstance(doc.content, str)
    assert len(doc.content) > 0
    assert doc.file_path == Path(sample_file_path)

def test_document_metadata(sample_file_path: str):
    """測試文件元數據提取"""
    doc = Document.from_file(sample_file_path)

    # 驗證基本元數據
    assert doc.title == "臺灣臺北地方法院民事判決"
    assert doc.case_number == "111年度訴字第456號"
    assert doc.date == "111年12月15日"

    # 驗證當事人信息
    parties = doc.get_parties()
    assert "原告" in parties
    assert parties["原告"] == "張三"
    assert "被告" in parties
    assert parties["被告"] == "李四"

def test_document_sections(sample_file_path: str):
    """測試文件段落分析"""
    doc = Document.from_file(sample_file_path)
    sections = doc.get_sections()

    # 驗證主要段落
    assert "主文" in sections
    assert "事實及理由" in sections
    assert len(sections) > 0

def test_contract_parsing(sample_contract_path: str):
    """測試合約文件解析"""
    doc = Document.from_file(sample_contract_path)

    # 驗證合約基本信息
    assert "房屋租賃契約" in doc.content

    # 驗證合約條款
    sections = doc.get_sections()
    assert "第一條" in sections
    assert "第二條" in sections
    assert "第三條" in sections

def test_invalid_file():
    """測試無效文件處理"""
    with pytest.raises(DocumentError):
        Document.from_file("non_existent_file.txt")

def test_empty_file(tmp_path):
    """測試空文件處理"""
    # 創建臨時空文件
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    with pytest.raises(DocumentError):
        Document.from_file(str(empty_file))

def test_document_text_processing(sample_file_path: str):
    """測試文件文本處理功能"""
    doc = Document.from_file(sample_file_path)

    # 測試分段
    paragraphs = doc.get_paragraphs()
    assert isinstance(paragraphs, list)
    assert len(paragraphs) > 0

    # 測試關鍵詞提取
    keywords = doc.extract_keywords()
    assert isinstance(keywords, list)
    assert len(keywords) > 0

    # 測試文本清理
    cleaned_text = doc.get_cleaned_text()
    assert isinstance(cleaned_text, str)
    assert len(cleaned_text) > 0
    assert "  " not in cleaned_text  # 確保沒有多餘的空格

def test_document_comparison(sample_file_path: str, sample_contract_path: str):
    """測試文件比較功能"""
    doc1 = Document.from_file(sample_file_path)
    doc2 = Document.from_file(sample_contract_path)

    # 測試相似度計算
    similarity = doc1.calculate_similarity(doc2)
    assert isinstance(similarity, float)
    assert 0 <= similarity <= 1

    # 測試差異比較
    diff = doc1.compare_with(doc2)
    assert isinstance(diff, dict)
    assert "additions" in diff
    assert "deletions" in diff
