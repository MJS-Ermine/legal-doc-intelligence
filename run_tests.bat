@echo off
setlocal enabledelayedexpansion

:: 設置編碼為 UTF-8
chcp 65001 > nul

echo 正在設置測試環境...

:: 檢查 Python 環境
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [錯誤] 未找到 Python，請確保 Python 已安裝並添加到 PATH 中
    exit /b 1
)

:: 檢查虛擬環境
if not exist "venv" (
    echo 創建虛擬環境...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [錯誤] 創建虛擬環境失敗
        exit /b 1
    )
)

:: 激活虛擬環境
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [錯誤] 激活虛擬環境失敗
    exit /b 1
)

:: 設置環境變量
set PYTHONPATH=%CD%
set PYTHONIOENCODING=utf-8

:: 安裝/更新依賴
echo 安裝/更新依賴...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [錯誤] 安裝依賴失敗
    exit /b 1
)

:: 運行環境設置腳本
echo 運行環境設置腳本...
python tests\setup_test_env.py
if %errorlevel% neq 0 (
    echo [錯誤] 環境設置失敗
    exit /b 1
)

:: 運行測試
echo 開始運行測試...
pytest tests\ -v --cov=src --cov-report=html --cov-report=term-missing
set TEST_EXIT_CODE=%errorlevel%

:: 生成覆蓋率報告
echo 生成測試覆蓋率報告...
coverage html

:: 退出虛擬環境
deactivate

:: 如果測試失敗，顯示錯誤信息
if %TEST_EXIT_CODE% neq 0 (
    echo [警告] 部分測試未通過，請查看上方錯誤信息
    exit /b %TEST_EXIT_CODE%
)

echo 測試完成！
echo 覆蓋率報告已生成在 htmlcov 目錄中

exit /b 0 