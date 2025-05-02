# syntax=docker/dockerfile:1
FROM python:3.10-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製 Poetry 並安裝
RUN pip install poetry

# 複製專案檔案
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi
COPY . .

# 預設啟動 FastAPI 服務
CMD ["uvicorn", "src.legal_doc_intelligence.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 設置環境變量
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000 