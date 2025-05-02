# Legal Document Intelligence Platform

[![CI](https://github.com/MJS-Ermine/legal-doc-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/MJS-Ermine/legal-doc-intelligence/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MJS-Ermine/legal-doc-intelligence/branch/main/graph/badge.svg)](https://codecov.io/gh/MJS-Ermine/legal-doc-intelligence)

法律文件智能處理平台，提供文件分析、向量化存儲和智能問答功能。

## 功能特點

- 文件處理和分析
- 向量化存儲（使用 FAISS）
- 智能問答系統（基於 RAG）
- REST API 接口

## 快速開始

### 安裝

```bash
# 克隆專案
git clone https://github.com/MJS-Ermine/legal-doc-intelligence.git
cd legal-doc-intelligence

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 運行

```bash
# 運行 API 服務
uvicorn legal_doc_intelligence.api.main:app --reload
```

訪問 http://localhost:8000/docs 查看 API 文檔。

## 開發

### 測試

```bash
# 運行測試
pytest

# 運行測試並生成覆蓋率報告
pytest --cov=legal_doc_intelligence --cov-report=html
```

### 代碼品質

```bash
# 運行代碼檢查
ruff check .
```

## API 文檔

主要 API 端點：

- `POST /api/v1/documents`: 上傳和處理文件
- `POST /api/v1/question`: 提交法律問題
- `POST /api/v1/analyze`: 分析文件

詳細 API 文檔請參考 Swagger UI：http://localhost:8000/docs

## 授權

本專案採用 MIT 授權協議。
