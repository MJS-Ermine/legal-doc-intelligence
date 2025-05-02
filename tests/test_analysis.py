"""
測試文本分析模組的功能
"""
from typing import List

import pytest

from legal_doc_intelligence.analysis import TextAnalyzer
from legal_doc_intelligence.document import Document


@pytest.fixture
def sample_documents() -> List[Document]:
    """準備測試用的文件樣本"""
    docs = [
        Document.from_file("examples/case1.txt"),
        Document.from_file("examples/case2.txt"),
        Document.from_file("examples/contract1.txt")
    ]
    return docs

@pytest.fixture
def analyzer() -> TextAnalyzer:
    """創建分析器實例"""
    return TextAnalyzer()

def test_extract_common_entities(analyzer: TextAnalyzer, sample_documents: List[Document]):
    """測試實體提取功能"""
    entities = analyzer.extract_common_entities(sample_documents)

    # 驗證基本實體類型是否存在
    assert "PERSON" in entities
    assert "ORG" in entities
    assert "LAW" in entities

    # 驗證特定實體是否被正確識別
    persons = entities["PERSON"]
    assert "張三" in persons
    assert "李四" in persons
    assert "王五" in persons

    # 驗證法條引用
    laws = entities["LAW"]
    assert "民法第367條" in laws
    assert "民法第437條" in laws

def test_extract_citations(analyzer: TextAnalyzer, sample_documents: List[Document]):
    """測試引用提取功能"""
    citations = analyzer.extract_common_citations(sample_documents)

    # 驗證是否提取到所有法條引用
    assert len(citations) >= 2
    assert any("民法第367條" in citation for citation in citations)
    assert any("民法第437條" in citation for citation in citations)

def test_create_merged_timeline(analyzer: TextAnalyzer, sample_documents: List[Document]):
    """測試時間軸生成功能"""
    timeline = analyzer.create_merged_timeline(sample_documents)

    # 驗證時間軸格式
    assert isinstance(timeline, list)
    for event in timeline:
        assert "date" in event
        assert "description" in event

    # 驗證特定事件
    dates = [event["date"] for event in timeline]
    assert "111年3月1日" in dates  # 第一個案例的購屋日期
    assert "111年5月1日" in dates  # 第二個案例的租賃日期

def test_cluster_documents(analyzer: TextAnalyzer, sample_documents: List[Document]):
    """測試文件聚類功能"""
    clusters = analyzer.cluster_documents(sample_documents)

    # 驗證基本聚類結構
    assert isinstance(clusters, dict)
    assert len(clusters) > 0

    # 驗證聚類結果
    all_docs = []
    for cluster in clusters.values():
        assert isinstance(cluster, list)
        all_docs.extend(cluster)

    # 確保所有文件都被分類
    assert len(all_docs) == len(sample_documents)

def test_extract_key_concepts(analyzer: TextAnalyzer, sample_documents: List[Document]):
    """測試關鍵概念提取功能"""
    concepts = analyzer.extract_key_concepts(sample_documents)

    # 驗證結果格式
    assert isinstance(concepts, dict)

    # 驗證關鍵概念
    concept_list = list(concepts.keys())
    assert any("租賃" in concept for concept in concept_list)
    assert any("買賣" in concept for concept in concept_list)
    assert any("契約" in concept for concept in concept_list)

def test_empty_documents(analyzer: TextAnalyzer):
    """測試空文件列表的處理"""
    empty_docs: List[Document] = []

    # 驗證各個方法對空輸入的處理
    assert analyzer.extract_common_entities(empty_docs) == {}
    assert analyzer.extract_common_citations(empty_docs) == []
    assert analyzer.create_merged_timeline(empty_docs) == []
    assert analyzer.cluster_documents(empty_docs) == {}
    assert analyzer.extract_key_concepts(empty_docs) == {}
