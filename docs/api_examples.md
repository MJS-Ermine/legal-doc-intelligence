# API 請求與回應範例

## 1. 上傳文件

**請求：**
```http
POST /api/v1/documents
Content-Type: multipart/form-data

file=@test.docx
```
**回應：**
```json
{
  "filename": "test.docx",
  "status": "uploaded"
}
```

## 2. 法律問答

**請求：**
```http
POST /api/v1/question
Content-Type: application/json

{
  "question": "什麼是民法第359條？"
}
```
**回應：**
```json
{
  "question": "什麼是民法第359條？",
  "answer": "(mock answer)"
}
```

## 3. 文檔分析

**請求：**
```http
POST /api/v1/analyze
Content-Type: application/json

{
  "doc_id": 123
}
```
**回應：**
```json
{
  "doc_id": 123,
  "analysis": "(mock analysis)"
}
``` 