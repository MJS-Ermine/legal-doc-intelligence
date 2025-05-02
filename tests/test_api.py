"""Unit tests for the Legal Document Intelligence Platform API endpoints."""

from fastapi.testclient import TestClient

from legal_doc_intelligence.api.main import app
from legal_doc_intelligence.database.models import DocumentType

# 創建測試客戶端
client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "timestamp" in response.json()

def test_answer_question():
    """Test the question answering endpoint."""
    # 準備測試數據
    test_data = {
        "question": "民法第一條的內容是什麼？",
        "filters": {"doc_type": "law"},
        "n_documents": 3
    }

    # 發送請求
    response = client.post("/api/v1/question", json=test_data)

    # 驗證響應
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, dict)
    assert "answer" in result
    assert "retrieved_documents" in result
    assert len(result["retrieved_documents"]) <= test_data["n_documents"]

def test_analyze_document():
    """Test the document analysis endpoint."""
    # 準備測試數據
    test_data = {
        "content": """民事判決
        臺灣臺北地方法院
        原告 張三
        被告 李四
        主文
        被告應給付原告新臺幣十萬元。
        事實及理由
        原告主張被告未依約給付貨款。""",
        "analysis_type": "summary"
    }

    # 發送請求
    response = client.post("/api/v1/analyze", json=test_data)

    # 驗證響應
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, dict)
    assert "analysis" in result
    assert "metadata" in result
    assert "entities" in result

    # 驗證實體提取結果
    assert "PERSON" in result["entities"]
    assert "張三" in result["entities"]["PERSON"]
    assert "李四" in result["entities"]["PERSON"]

def test_upload_document():
    """Test the document upload endpoint."""
    # 準備測試數據
    test_data = {
        "content": """民事判決
        臺灣臺北地方法院
        原告 張三
        被告 李四
        主文
        被告應給付原告新臺幣十萬元。""",
        "doc_type": DocumentType.JUDGMENT,
        "title": "110年度重訴字第123號",
        "source_url": "https://judgment.judicial.gov.tw/FJUD/data/123.html",
        "metadata": {
            "court": "臺灣臺北地方法院",
            "case_number": "110年度重訴字第123號",
            "judge": "王法官"
        }
    }

    # 發送請求
    response = client.post("/api/v1/documents", json=test_data)

    # 驗證響應
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, dict)
    assert "document_id" in result
    assert "metadata" in result
    assert "entities" in result
    assert "status" in result
    assert result["status"] == "success"

def test_invalid_question():
    """Test handling of invalid question request."""
    # 準備無效的測試數據
    test_data = {
        "filters": {"doc_type": "law"},
        "n_documents": 3
    }

    # 發送請求
    response = client.post("/api/v1/question", json=test_data)

    # 驗證錯誤響應
    assert response.status_code == 422  # Unprocessable Entity

def test_invalid_document_type():
    """Test handling of invalid document type."""
    # 準備無效的測試數據
    test_data = {
        "content": "測試文件內容",
        "doc_type": "INVALID_TYPE",  # 無效的文件類型
        "title": "測試文件",
        "source_url": "https://example.com/test.html"
    }

    # 發送請求
    response = client.post("/api/v1/documents", json=test_data)

    # 驗證錯誤響應
    assert response.status_code == 422  # Unprocessable Entity
