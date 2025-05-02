"""Test package initialization."""

import os
import sys
from pathlib import Path

# 添加源代碼目錄到 Python 路徑
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 設置測試環境變量
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("POSTGRES_DB", "test_legal_doc_db")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")

# 設置測試數據目錄
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)

# 設置日誌目錄
LOG_DIR = TEST_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 設置其他必要的目錄
for dir_name in ["uploads", "processed", "vector_db"]:
    (TEST_DATA_DIR / dir_name).mkdir(exist_ok=True)
