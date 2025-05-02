
from sqlalchemy import create_engine, text
from sqlalchemy_utils import create_database, database_exists

# 數據庫連接配置
DB_USER = "postgres"
DB_PASSWORD = "lingetzlan4586"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "legal_doc_db"

# 創建連接 URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    # 創建引擎連接到 postgres 數據庫
    engine = create_engine(DATABASE_URL)

    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"數據庫 '{DB_NAME}' 創建成功！")
    else:
        print(f"數據庫 '{DB_NAME}' 已存在。")

    # 測試連接
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print("成功連接到新數據庫！")
        print(f"PostgreSQL 版本: {version}")

except Exception as e:
    print("操作過程中出錯：")
    print(e)
