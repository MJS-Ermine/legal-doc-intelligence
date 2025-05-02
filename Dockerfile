# Use Python 3.10 slim image as base
FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製專案文件
COPY . .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -e .

# 設置環境變量
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "legal_doc_intelligence.api.main:app", "--host", "0.0.0.0", "--port", "8000"] 