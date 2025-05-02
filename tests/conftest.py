"""Test configuration and shared fixtures."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from legal_doc_intelligence.api.main import app
from legal_doc_intelligence.database.models import Base
from legal_doc_intelligence.evaluation.evaluator import LegalEvaluator
from legal_doc_intelligence.processors.text_processor import LegalTextProcessor


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent / "test_data"

@pytest.fixture(scope="session")
def sample_legal_documents() -> Dict[str, str]:
    """提供測試用的法律文件樣本。"""
    return {
        "judgment": """臺灣臺北地方法院民事判決
        110年度訴字第123號
        原告 張三
        被告 李四
        主文
        被告應給付原告新臺幣十萬元。
        事實及理由
        原告主張被告未依約給付貨款。""",

        "contract": """買賣契約書
        立契約書人：
        買方：張三
        賣方：李四
        第一條 買賣標的物
        一般商品一批，詳如附件清單。
        第二條 價金及付款
        總價金新臺幣十萬元整。""",

        "law": """民法第一條
        民事，法律所未規定者，依習慣；無習慣者，依法理。
        民法第二條
        民事所適用之習慣，以不背於公共秩序或善良風俗者為限。"""
    }

@pytest.fixture(scope="session")
def sample_metadata() -> Dict[str, Dict[str, Any]]:
    """提供測試用的元數據樣本。"""
    return {
        "judgment": {
            "case_number": "110年度訴字第123號",
            "court": "臺灣臺北地方法院",
            "case_type": "民事",
            "date": datetime(2021, 1, 1).isoformat()
        },
        "contract": {
            "type": "買賣契約",
            "parties": ["張三", "李四"],
            "date": datetime(2021, 1, 1).isoformat()
        },
        "law": {
            "name": "民法",
            "articles": ["第一條", "第二條"],
            "category": "民事"
        }
    }

@pytest.fixture(scope="session")
def temp_test_dir():
    """提供臨時測試目錄。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture(scope="function")
def processor():
    """提供文本處理器實例。"""
    return LegalTextProcessor()

@pytest.fixture(scope="function")
def evaluator():
    """提供評估器實例。"""
    return LegalEvaluator()

@pytest.fixture(scope="session")
def test_database_url():
    """提供測試數據庫 URL。"""
    return "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    return create_engine("sqlite:///:memory:", echo=False)

@pytest.fixture(scope="session")
def tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine, tables) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API calls."""
    class MockResponse:
        def json(self):
            return {
                "choices": [{
                    "text": "這是一個測試回應。",
                    "message": {"content": "這是一個測試回應。"}
                }]
            }

    def mock_completion(*args, **kwargs):
        return MockResponse()

    # 替換 OpenAI API 調用
    if hasattr(monkeypatch, "setattr"):
        monkeypatch.setattr(
            "openai.Completion.create",
            mock_completion
        )
        monkeypatch.setattr(
            "openai.ChatCompletion.create",
            mock_completion
        )

@pytest.fixture
def mock_embeddings(monkeypatch):
    """Mock embedding generation."""
    def mock_encode(*args, **kwargs):
        return [[0.1] * 384]  # 模擬 384 維的嵌入向量

    # 替換嵌入模型
    if hasattr(monkeypatch, "setattr"):
        monkeypatch.setattr(
            "sentence_transformers.SentenceTransformer.encode",
            mock_encode
        )

def pytest_configure(config):
    """配置測試環境。"""
    # 創建測試數據目錄
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    # 生成測試數據文件
    sample_data = {
        "documents": {
            "judgment": "臺灣臺北地方法院民事判決\n110年度訴字第123號\n...",
            "contract": "買賣契約書\n立契約書人：\n...",
            "law": "民法第一條\n民事，法律所未規定者，依習慣；無習慣者，依法理。\n..."
        },
        "metadata": {
            "judgment": {"case_number": "110年度訴字第123號", "court": "臺灣臺北地方法院"},
            "contract": {"type": "買賣契約", "parties": ["張三", "李四"]},
            "law": {"name": "民法", "articles": ["第一條"]}
        }
    }

    with open(test_data_dir / "test_data.json", "w", encoding="utf-8") as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
