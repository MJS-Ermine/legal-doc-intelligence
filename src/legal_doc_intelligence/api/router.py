"""FastAPI router for document processing and search endpoints."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.models import Document, DocumentType
from ..database.session import get_db
from ..pipeline.data_pipeline import DataPipeline, PipelineConfig
from ..processors.document_processor import DocumentProcessor
from ..processors.vectorization_processor import VectorizationProcessor
from ..rag.legal_rag import LegalRAG

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["documents"])

# Initialize components
VECTOR_STORE_DIR = Path("data/vector_store")
PIPELINE_DIR = Path("data/pipeline")

document_processor = DocumentProcessor(persist_directory=VECTOR_STORE_DIR)
vectorization_processor = VectorizationProcessor(vector_store=document_processor.vector_store)
rag_system = LegalRAG(document_processor=document_processor)

# Initialize pipeline
pipeline_config = PipelineConfig(
    chunk_size=500,
    chunk_overlap=50,
    max_workers=4,
    batch_size=100,
    source_tracking=True
)

pipeline = DataPipeline(
    config=pipeline_config,
    document_processor=document_processor,
    vectorization_processor=vectorization_processor,
    persist_dir=PIPELINE_DIR
)

class DocumentRequest(BaseModel):
    """Request model for document processing."""

    text: str
    doc_id: str
    case_type: str
    court: str
    date: datetime
    source: str
    title: str

class BatchDocumentRequest(BaseModel):
    """Request model for batch document processing."""

    documents: List[DocumentRequest]
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None

class SearchRequest(BaseModel):
    """Request model for document search."""

    query: str
    k: Optional[int] = None
    min_score: float = 0.3
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    """Response model for search results."""

    document: str
    doc_metadata: dict
    score: float
    context: Optional[str] = None

class PipelineResponse(BaseModel):
    """Response model for pipeline operations."""

    request_id: str
    status: str
    stats: Optional[Dict[str, Any]] = None

class RAGRequest(BaseModel):
    query: str
    k: int = 4
    min_score: float = 0.3
    mode: str = "default"

class RAGResponse(BaseModel):
    response: str
    sources: list

@router.post("/documents", response_model=str)
async def process_document(
    request: DocumentRequest,
    db: Session = Depends(get_db)
) -> str:
    """Process and store a document.
    
    Args:
        request: Document processing request.
        db: Database session.
        
    Returns:
        Document ID.
    """
    try:
        # Create document record
        document = Document(
            doc_type=DocumentType(request.case_type),
            title=request.title,
            content=request.text,
            source_url=request.source,
            court_name=request.court,
            decision_date=request.date
        )
        db.add(document)
        db.commit()

        # Process document through pipeline
        doc_ids = await pipeline.process_batch(
            documents=[document],
            db=db
        )

        if not doc_ids:
            raise HTTPException(
                status_code=500,
                detail="Failed to process document"
            )

        return doc_ids[0]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

@router.post("/documents/batch", response_model=PipelineResponse)
async def process_documents_batch(
    request: BatchDocumentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> PipelineResponse:
    """Process multiple documents in the background.
    
    Args:
        request: Batch document processing request.
        background_tasks: FastAPI background tasks.
        db: Database session.
        
    Returns:
        Pipeline response with request ID.
    """
    request_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        # Update pipeline config if provided
        if request.chunk_size:
            pipeline.config.chunk_size = request.chunk_size
        if request.chunk_overlap:
            pipeline.config.chunk_overlap = request.chunk_overlap

        # Create document records
        documents = []
        for doc_request in request.documents:
            document = Document(
                doc_type=DocumentType(doc_request.case_type),
                title=doc_request.title,
                content=doc_request.text,
                source_url=doc_request.source,
                court_name=doc_request.court,
                decision_date=doc_request.date
            )
            db.add(document)
            documents.append(document)

        db.commit()

        # Process documents in background
        async def process_batch() -> None:
            await pipeline.process_batch(documents=documents, db=db)

        background_tasks.add_task(process_batch)

        return PipelineResponse(
            request_id=request_id,
            status="pending"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing batch: {str(e)}"
        )

@router.get("/documents/batch/{request_id}", response_model=PipelineResponse)
def get_batch_status(request_id: str) -> PipelineResponse:
    """Get status of a batch processing request.
    
    Args:
        request_id: Batch request ID.
        
    Returns:
        Pipeline response with status and stats.
    """
    stats = pipeline.get_stats()

    status = "completed"
    if stats["failed_documents"] > 0:
        if stats["processed_documents"] > 0:
            status = "partially_completed"
        else:
            status = "failed"
    elif stats["processed_documents"] < stats["total_documents"]:
        status = "in_progress"

    return PipelineResponse(
        request_id=request_id,
        status=status,
        stats=stats
    )

@router.post("/search", response_model=List[SearchResult])
async def search_documents(
    request: SearchRequest,
    context_size: Optional[int] = Query(None, gt=0, le=500)
) -> List[SearchResult]:
    """Search for similar documents with advanced options.
    
    Args:
        request: Search request.
        context_size: Optional number of characters to include before/after match.
        
    Returns:
        List of search results.
    """
    try:
        results = document_processor.search_similar(
            query=request.query,
            k=request.k or 4,
            filter_metadata=request.filters
        )

        formatted_results = []
        for result in results:
            score = 1.0 - (result.get("distance", 0) or 0)
            if score >= request.min_score:
                # Add context if requested
                context = None
                if context_size and request.query in result["document"]:
                    idx = result["document"].index(request.query)
                    start = max(0, idx - context_size)
                    end = min(len(result["document"]), idx + len(request.query) + context_size)
                    context = result["document"][start:end]

                formatted_results.append(
                    SearchResult(
                        document=result["document"],
                        doc_metadata=result["metadata"],
                        score=score,
                        context=context
                    )
                )

        return formatted_results

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )

@router.post("/rag/query", response_model=RAGResponse)
async def rag_query(request: RAGRequest) -> RAGResponse:
    """Process a RAG query.
    
    Args:
        request: RAG query request.
        
    Returns:
        Generated response and source documents.
    """
    try:
        if request.mode == "summary":
            response, documents = rag_system.summarize(
                query=request.query,
                k=request.k,
                min_score=request.min_score
            )
        else:
            response, documents = rag_system.query(
                query=request.query,
                k=request.k,
                min_score=request.min_score
            )

        # Format source documents
        sources = [
            {
                "content": doc.page_content,
                "doc_metadata": doc.metadata,
                "score": doc.metadata.get("score", 0)
            }
            for doc in documents
        ]

        return RAGResponse(
            response=response,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing RAG query: {str(e)}"
        )
