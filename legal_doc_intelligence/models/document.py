from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class LegalDocument(Base):
    """法律文件基礎模型
    
    用於存儲從各來源爬取的法律文件，包含原始內容和結構化數據
    """
    __tablename__ = 'legal_documents'

    id = Column(Integer, primary_key=True)
    doc_id = Column(String(100), unique=True, nullable=False, comment='文件唯一識別碼')
    title = Column(String(500), nullable=False, comment='文件標題')
    court = Column(String(100), nullable=False, comment='法院名稱')
    case_number = Column(String(100), nullable=False, comment='案號')
    case_type = Column(String(50), nullable=False, comment='案件類型')
    judgment_date = Column(DateTime, nullable=False, comment='判決日期')

    raw_content = Column(Text, nullable=False, comment='原始文件內容')
    processed_content = Column(JSON, comment='結構化處理結果')
    metadata = Column(JSON, comment='額外元數據')

    created_at = Column(DateTime, default=datetime.utcnow, comment='創建時間')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新時間')

    # 關聯
    citations = relationship("Citation", back_populates="document")
    parties = relationship("Party", back_populates="document")

class Citation(Base):
    """引用條文模型"""
    __tablename__ = 'citations'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('legal_documents.id'))
    law_name = Column(String(200), nullable=False, comment='法規名稱')
    article = Column(String(100), nullable=False, comment='條文編號')
    content = Column(Text, comment='條文內容')

    document = relationship("LegalDocument", back_populates="citations")

class Party(Base):
    """當事人模型（經過脫敏）"""
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('legal_documents.id'))
    party_type = Column(String(50), nullable=False, comment='當事人類型')
    masked_name = Column(String(100), nullable=False, comment='脫敏後名稱')

    document = relationship("LegalDocument", back_populates="parties")
