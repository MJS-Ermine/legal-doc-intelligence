from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.document import LegalDocument
from ..schemas import CitationResponse, DocumentList, DocumentResponse, SearchQuery

app = FastAPI(
    title="法律文件智能處理平台",
    description="提供法律文件的存儲、檢索和分析功能",
    version="1.0.0"
)

@app.get("/documents/", response_model=List[DocumentList])
async def list_documents(
    db: Session = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    court: Optional[str] = None,
    case_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """獲取判決書列表

    可以通過法院、案件類型和日期範圍進行過濾
    """
    if db is None:
        db = next(get_db())

    query = db.query(LegalDocument)

    if court:
        query = query.filter(LegalDocument.court == court)
    if case_type:
        query = query.filter(LegalDocument.case_type == case_type)
    if start_date:
        query = query.filter(LegalDocument.judgment_date >= start_date)
    if end_date:
        query = query.filter(LegalDocument.judgment_date <= end_date)

    query.count()
    documents = query.offset(skip).limit(limit).all()

    return [
        DocumentList(
            id=doc.id,
            doc_id=doc.doc_id,
            title=doc.title,
            court=doc.court,
            case_number=doc.case_number,
            judgment_date=doc.judgment_date
        )
        for doc in documents
    ]

@app.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: Session = None):
    """獲取單個判決書詳情"""
    if db is None:
        db = next(get_db())

    document = db.query(LegalDocument).filter(LegalDocument.doc_id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.get("/documents/{doc_id}/citations", response_model=List[CitationResponse])
async def get_document_citations(doc_id: str, db: Session = None):
    """獲取判決書引用的法條"""
    if db is None:
        db = next(get_db())

    document = db.query(LegalDocument).filter(LegalDocument.doc_id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document.citations

@app.post("/search/", response_model=List[DocumentList])
async def search_documents(
    query: SearchQuery,
    db: Session = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """搜索判決書

    支持全文搜索和條件過濾
    """
    if db is None:
        db = next(get_db())

    base_query = db.query(LegalDocument)

    # 關鍵詞搜索
    if query.keyword:
        base_query = base_query.filter(
            LegalDocument.raw_content.ilike(f"%{query.keyword}%")
        )

    # 條件過濾
    if query.court:
        base_query = base_query.filter(LegalDocument.court == query.court)
    if query.case_type:
        base_query = base_query.filter(LegalDocument.case_type == query.case_type)
    if query.start_date:
        base_query = base_query.filter(LegalDocument.judgment_date >= query.start_date)
    if query.end_date:
        base_query = base_query.filter(LegalDocument.judgment_date <= query.end_date)

    base_query.count()
    documents = base_query.offset(skip).limit(limit).all()

    return [
        DocumentList(
            id=doc.id,
            doc_id=doc.doc_id,
            title=doc.title,
            court=doc.court,
            case_number=doc.case_number,
            judgment_date=doc.judgment_date
        )
        for doc in documents
    ]
