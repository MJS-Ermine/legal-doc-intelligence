"""默認配置文件"""
import os
from pathlib import Path

# 項目根目錄
BASE_DIR = Path(__file__).parent.parent

# 數據庫配置
DATABASE = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "legal_doc_db"),
}

# API 配置
API = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "8000")),
    "debug": os.getenv("DEBUG", "true").lower() == "true",
}

# 向量存儲配置
VECTOR_STORE = {
    "directory": os.getenv("VECTOR_STORE_DIR", str(BASE_DIR / "data/vector_store")),
    "model_cache": os.getenv("MODEL_CACHE_DIR", str(BASE_DIR / "data/model_cache")),
}

# 日誌配置
LOGGING = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "directory": os.getenv("LOG_DIR", str(BASE_DIR / "logs")),
}

# 安全配置
SECURITY = {
    "secret_key": os.getenv("SECRET_KEY", "your-secret-key-here"),
    "allowed_origins": eval(os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000"]')),
}
