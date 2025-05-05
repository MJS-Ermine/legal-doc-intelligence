"""項目初始化腳本"""
import os
from pathlib import Path


def create_directory_structure():
    """創建項目目錄結構"""
    directories = [
        "data/vector_store",
        "data/model_cache",
        "logs",
        "tests/data",
        "docs/api",
        "docs/user_guide",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def setup_environment():
    """設置開發環境"""
    try:
        pass
    except ImportError:
        print("Installing poetry...")
        os.system("pip install poetry")

    print("Installing dependencies...")
    os.system("poetry install")

    print("Setting up pre-commit hooks...")
    os.system("poetry run pre-commit install")

def init_database():
    """初始化數據庫"""
    from legal_doc_intelligence.database import init_db

    print("Initializing database...")
    init_db()

def main():
    """主函數"""
    print("Initializing Legal Document Intelligence Platform...")

    # 創建目錄結構
    create_directory_structure()

    # 設置環境
    setup_environment()

    # 初始化數據庫
    init_database()

    print("\nInitialization completed successfully!")

if __name__ == "__main__":
    main()
