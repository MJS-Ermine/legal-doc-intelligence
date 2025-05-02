"""Test utilities and helper functions."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_test_data(file_path: str) -> Dict[str, Any]:
    """從 JSON 文件加載測試數據。"""
    path = Path(__file__).parent / "test_data" / file_path
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def create_test_document(
    doc_type: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """創建測試文檔。"""
    return {
        "doc_type": doc_type,
        "content": content,
        "metadata": metadata or {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def compare_documents(doc1: Dict[str, Any], doc2: Dict[str, Any]) -> bool:
    """比較兩個文檔是否相同（忽略時間戳）。"""
    keys_to_compare = ["doc_type", "content", "metadata"]
    return all(doc1.get(k) == doc2.get(k) for k in keys_to_compare)

def setup_test_directories() -> Dict[str, Path]:
    """設置測試目錄結構。"""
    test_root = Path(__file__).parent
    dirs = {
        "data": test_root / "test_data",
        "logs": test_root / "logs",
        "uploads": test_root / "test_data" / "uploads",
        "processed": test_root / "test_data" / "processed",
        "vector_db": test_root / "test_data" / "vector_db"
    }

    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dirs

def cleanup_test_files(paths: List[Path]) -> None:
    """清理測試文件。"""
    for path in paths:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()

def get_test_file_path(filename: str) -> Path:
    """獲取測試文件的完整路徑。"""
    return Path(__file__).parent / "test_data" / filename

def create_test_env() -> None:
    """創建測試環境。"""
    # 創建必要的目錄
    dirs = setup_test_directories()

    # 創建測試數據文件
    test_data = {
        "documents": {
            "judgment": {
                "content": "測試判決書內容",
                "metadata": {"case_number": "TEST-2024-001"}
            },
            "contract": {
                "content": "測試契約內容",
                "metadata": {"parties": ["甲方", "乙方"]}
            }
        }
    }

    with open(dirs["data"] / "test_data.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
