# 貢獻指南

感謝您考慮為法律文件智能處理平台做出貢獻！本文檔將指導您如何參與專案開發。

## 開發環境設置

1. Fork 並克隆專案：
```bash
git clone https://github.com/yourusername/legal-doc-intelligence.git
cd legal-doc-intelligence
```

2. 創建虛擬環境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安裝依賴：
```bash
pip install -r requirements.txt
pip install -e .
```

## 代碼風格指南

我們使用 `ruff` 進行代碼格式化和檢查：

```bash
# 檢查代碼風格
ruff check .

# 自動修復
ruff check --fix .
```

### Python 版本
- 使用 Python 3.10 或更高版本
- 使用類型註解
- 遵循 PEP 8 規範

### 文檔規範
- 所有函數、類和模塊都必須有文檔字符串
- 使用 Google 風格的文檔字符串格式
- 包含參數說明、返回值和示例

## 提交規範

### 分支命名
- 功能分支：`feature/描述`
- 修復分支：`fix/描述`
- 文檔分支：`docs/描述`
- 優化分支：`optimize/描述`

### 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

類型（type）：
- feat: 新功能
- fix: 錯誤修復
- docs: 文檔更改
- style: 格式調整
- refactor: 代碼重構
- test: 測試相關
- chore: 構建過程或輔助工具的變動

### Pull Request 流程

1. 確保本地分支與主分支同步
2. 創建功能分支
3. 提交更改
4. 運行測試確保全部通過
5. 推送到您的 Fork
6. 創建 Pull Request

## 測試指南

### 運行測試
```bash
# 運行所有測試
pytest

# 運行特定測試
pytest tests/test_api.py

# 生成測試覆蓋率報告
pytest --cov=legal_doc_intelligence --cov-report=html
```

### 測試要求
- 所有新功能必須包含測試
- 修復錯誤時必須添加相應的測試用例
- 測試覆蓋率必須達到 80% 以上
- 集成測試和單元測試都是必要的

## 文檔貢獻

### API 文檔
- 使用 OpenAPI/Swagger 規範
- 保持示例代碼最新
- 包含請求/響應示例

### 用戶指南
- 確保示例可以運行
- 提供清晰的步驟說明
- 包含常見問題解答

## 安全問題報告

如果您發現安全漏洞，請不要創建公開的 Issue，而是發送郵件到 security@example.com。

## 行為準則

- 尊重所有貢獻者
- 保持專業和友善的交流
- 接受建設性的批評
- 專注於專案目標

## 獲取幫助

- 查看 [文檔](docs/)
- 提交 Issue
- 發送郵件到 support@example.com
- 加入我們的 [Slack 社群](https://example.com/slack)

再次感謝您的貢獻！ 