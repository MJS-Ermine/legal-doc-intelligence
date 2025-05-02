from sqlalchemy import create_engine, text

# 數據庫連接配置
DB_USER = "postgres"
DB_PASSWORD = "lingetzlan4586"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"  # 默認數據庫名

# 創建連接 URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    # 創建引擎
    engine = create_engine(DATABASE_URL)
    
    # 測試連接
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print("成功連接到數據庫！")
        print(f"PostgreSQL 版本: {version}")

except Exception as e:
    print("連接數據庫時出錯：")
    print(e) 