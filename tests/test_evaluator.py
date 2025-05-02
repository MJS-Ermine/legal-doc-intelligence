"""Unit tests for the Legal Document Intelligence Platform evaluator."""


import pytest

from legal_doc_intelligence.evaluation.evaluator import LegalEvaluator


@pytest.fixture
def evaluator():
    """Create an evaluator instance for testing."""
    return LegalEvaluator()

def test_evaluate_rag_response(evaluator):
    """Test RAG response evaluation."""
    # 準備測試數據
    question = "什麼是民法第一條的內容？"
    response = "民法第一條規定，民事，法律所未規定者，依習慣；無習慣者，依法理。"
    ground_truth = "民法第一條內容為：民事，法律所未規定者，依習慣；無習慣者，依法理。"
    retrieved_docs = [
        "民法第一條規定了法源的適用順序。",
        "在民事案件中，法官必須依據法律、習慣和法理來做出判決。"
    ]

    # 執行評估
    result = evaluator.evaluate_rag_response(
        question=question,
        response=response,
        ground_truth=ground_truth,
        retrieved_docs=retrieved_docs
    )

    # 驗證結果
    assert isinstance(result, dict)
    assert "rouge_scores" in result
    assert "bleu_score" in result
    assert "semantic_similarity" in result
    assert "retrieval_evaluation" in result
    assert "timestamp" in result

    # 驗證分數範圍
    assert 0 <= result["bleu_score"] <= 1
    assert 0 <= result["semantic_similarity"] <= 1

def test_evaluate_entity_extraction(evaluator):
    """Test entity extraction evaluation."""
    # 準備測試數據
    extracted_entities = {
        "PERSON": ["張三", "李四"],
        "ORG": ["最高法院", "台北地方法院"],
        "LAW": ["民法第一條", "刑法第二條"]
    }

    ground_truth_entities = {
        "PERSON": ["張三", "李四", "王五"],
        "ORG": ["最高法院", "台北地方法院"],
        "LAW": ["民法第一條", "刑法第二條", "民事訴訟法第三條"]
    }

    # 執行評估
    result = evaluator.evaluate_entity_extraction(
        extracted_entities=extracted_entities,
        ground_truth_entities=ground_truth_entities
    )

    # 驗證結果
    assert isinstance(result, dict)
    for entity_type in ["PERSON", "ORG", "LAW"]:
        assert entity_type in result
        assert "precision" in result[entity_type]
        assert "recall" in result[entity_type]
        assert "f1" in result[entity_type]

        # 驗證分數範圍
        assert 0 <= result[entity_type]["precision"] <= 1
        assert 0 <= result[entity_type]["recall"] <= 1
        assert 0 <= result[entity_type]["f1"] <= 1

def test_evaluate_document_segmentation(evaluator):
    """Test document segmentation evaluation."""
    # 準備測試數據
    segmented_doc = [
        {"type": "header", "content": "民事判決"},
        {"type": "facts", "content": "原告主張被告未依約給付貨款。"},
        {"type": "reasoning", "content": "本院審酌相關證據。"}
    ]

    ground_truth_segments = [
        {"type": "header", "content": "民事判決書"},
        {"type": "facts", "content": "原告主張被告未依約給付貨款。"},
        {"type": "reasoning", "content": "本院審酌所有證據。"}
    ]

    # 執行評估
    result = evaluator.evaluate_document_segmentation(
        segmented_doc=segmented_doc,
        ground_truth_segments=ground_truth_segments
    )

    # 驗證結果
    assert isinstance(result, dict)
    assert "type_accuracy" in result
    assert "content_similarity_mean" in result
    assert "content_similarity_std" in result

    # 驗證分數範圍
    assert 0 <= result["type_accuracy"] <= 1
    assert 0 <= result["content_similarity_mean"] <= 1

def test_evaluate_retrieval(evaluator):
    """Test document retrieval evaluation."""
    # 準備測試數據
    question = "民法中關於契約的規定有哪些？"
    retrieved_docs = [
        "民法第一百五十三條規定，當事人互相表示意思一致者，契約即為成立。",
        "關於契約的成立，民法有明確規定。",
        "契約自由原則是民法的重要原則之一。"
    ]

    # 執行評估
    result = evaluator._evaluate_retrieval(
        question=question,
        retrieved_docs=retrieved_docs
    )

    # 驗證結果
    assert isinstance(result, dict)
    assert "max_similarity" in result
    assert "mean_similarity" in result
    assert "min_similarity" in result

    # 驗證分數範圍
    assert 0 <= result["max_similarity"] <= 1
    assert 0 <= result["mean_similarity"] <= 1
    assert 0 <= result["min_similarity"] <= 1
    assert result["min_similarity"] <= result["mean_similarity"] <= result["max_similarity"]
