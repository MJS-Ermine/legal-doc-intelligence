"""FastAPI application for the Legal Document Intelligence Platform."""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database.db_manager import db_manager
from ..database.models import Document, DocumentType
from ..evaluation.evaluator import LegalEvaluator
from ..processors.text_processor import LegalTextProcessor
from ..processors.vectorization_processor import VectorizationProcessor
from ..rag.rag_system import LegalRAGSystem
from ..vectorstore import create_vector_store

# 初始化應用程序組件
app = FastAPI(
    title="Legal Document Intelligence API",
    description="API for legal document processing and question answering",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化處理器和系統組件
vector_store = create_vector_store()
text_processor = LegalTextProcessor()
vectorization_processor = VectorizationProcessor(vector_store)
rag_system = LegalRAGSystem(vectorization_processor)
evaluator = LegalEvaluator()

# Pydantic 模型
class QuestionRequest(BaseModel):
    """Question request model."""

    question: str = Field(..., description="The legal question to answer")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for document retrieval")
    n_documents: Optional[int] = Field(3, description="Number of documents to retrieve")

class DocumentRequest(BaseModel):
    """Document analysis request model."""

    content: str = Field(..., description="The document content to analyze")
    analysis_type: str = Field("summary", description="Type of analysis to perform")

class DocumentUploadRequest(BaseModel):
    """Document upload request model."""

    content: str = Field(..., description="The document content")
    doc_type: DocumentType = Field(..., description="Type of the document")
    title: str = Field(..., description="Document title")
    source_url: str = Field(..., description="Source URL of the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

# 依賴項
def get_db():
    """Get database session."""
    db = next(db_manager.get_db())
    try:
        yield db
    finally:
        db.close()

# API 端點
@app.post("/api/v1/question", response_model=Dict[str, Any])
async def answer_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Answer a legal question using the RAG system.
    
    Args:
        request: Question request containing the question and optional parameters.
        db: Database session.
        
    Returns:
        Answer and supporting information.
    """
    try:
        response = await rag_system.answer_question(
            question=request.question,
            n_documents=request.n_documents,
            filters=request.filters
        )

        return response

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze", response_model=Dict[str, Any])
async def analyze_document(
    request: DocumentRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Analyze a legal document.
    
    Args:
        request: Document analysis request.
        db: Database session.
        
    Returns:
        Analysis results.
    """
    try:
        # 處理文本
        cleaned_text = text_processor.clean_text(request.content)

        # 提取元數據
        metadata = text_processor.extract_metadata(cleaned_text)

        # 分析文檔
        analysis = await rag_system.analyze_legal_document(
            document_text=cleaned_text,
            analysis_type=request.analysis_type
        )

        # 提取實體
        entities = text_processor.extract_entities(cleaned_text)

        return {
            "analysis": analysis,
            "metadata": metadata,
            "entities": entities
        }

    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/documents", response_model=Dict[str, Any])
async def upload_document(
    request: DocumentUploadRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upload and process a new document.
    
    Args:
        request: Document upload request.
        db: Database session.
        
    Returns:
        Processing results and document ID.
    """
    try:
        # 清理文本
        cleaned_text = text_processor.clean_text(request.content)

        # 創建文檔記錄
        document = Document(
            doc_type=request.doc_type,
            title=request.title,
            content=cleaned_text,
            source_url=request.source_url,
            created_at=datetime.utcnow()
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # 處理文檔
        vectorization_processor.process_document(document, db)

        # 提取元數據和實體
        metadata = text_processor.extract_metadata(cleaned_text)
        entities = text_processor.extract_entities(cleaned_text)

        return {
            "document_id": document.id,
            "metadata": metadata,
            "entities": entities,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check() -> Dict[str, str]:
    """Check API health status.
    
    Returns:
        Health status information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
