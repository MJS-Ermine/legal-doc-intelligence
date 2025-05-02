from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """文件基礎模型"""
    title: str = Field(..., description="文件標題")
    court: str = Field(..., description="法院名稱")
    case_number: str = Field(..., description="案號")
    case_type: str = Field(..., description="案件類型")
    judgment_date: datetime = Field(..., description="判決日期")

class DocumentCreate(DocumentBase):
    """創建文件請求模型"""
    raw_content: str = Field(..., description="原始文件內容")
    processed_content: Optional[Dict[str, Any]] = Field(None, description="結構化處理結果")
    metadata: Optional[Dict[str, Any]] = Field(None, description="額外元數據")

class DocumentList(DocumentBase):
    """文件列表響應模型"""
    id: int = Field(..., description="文件ID")
    doc_id: str = Field(..., description="文件唯一識別碼")

    class Config:
        from_attributes = True

class CitationBase(BaseModel):
    """引用條文基礎模型"""
    law_name: str = Field(..., description="法規名稱")
    article: str = Field(..., description="條文編號")
    content: Optional[str] = Field(None, description="條文內容")

class CitationResponse(CitationBase):
    """引用條文響應模型"""
    id: int = Field(..., description="引用ID")
    document_id: int = Field(..., description="關聯文件ID")

    class Config:
        from_attributes = True

class PartyBase(BaseModel):
    """當事人基礎模型"""
    party_type: str = Field(..., description="當事人類型")
    masked_name: str = Field(..., description="脫敏後名稱")

class PartyResponse(PartyBase):
    """當事人響應模型"""
    id: int = Field(..., description="當事人ID")
    document_id: int = Field(..., description="關聯文件ID")

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    """文件詳情響應模型"""
    id: int = Field(..., description="文件ID")
    doc_id: str = Field(..., description="文件唯一識別碼")
    raw_content: str = Field(..., description="原始文件內容")
    processed_content: Optional[Dict[str, Any]] = Field(None, description="結構化處理結果")
    metadata: Optional[Dict[str, Any]] = Field(None, description="額外元數據")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")
    citations: List[CitationResponse] = Field(default_factory=list, description="引用法條")
    parties: List[PartyResponse] = Field(default_factory=list, description="當事人列表")

    class Config:
        from_attributes = True

class SearchQuery(BaseModel):
    """搜索請求模型"""
    keyword: Optional[str] = Field(None, description="搜索關鍵詞")
    court: Optional[str] = Field(None, description="法院名稱")
    case_type: Optional[str] = Field(None, description="案件類型")
    start_date: Optional[datetime] = Field(None, description="起始日期")
    end_date: Optional[datetime] = Field(None, description="結束日期")
