"""
FastAPI Backend for Multi-PDF RAG System
=========================================
Production-ready API for:
- Multiple PDF uploads with duplicate detection
- Question answering using RAG pipeline
- Document management
"""

import os
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_engine import RAGEngine

from dotenv import load_dotenv

# ============================================
# CONFIGURATION
# ============================================

# Load .env file
load_dotenv()

# Now read the API key from env
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize FastAPI app
app = FastAPI(
    title="Multi-PDF RAG System",
    description="Production-ready RAG application with persistent embeddings",
    version="1.0.0"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    # During local development allow all origins to avoid CORS issues.
    # For production, restrict this to your frontend origins.
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Engine (singleton)
rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Get or initialize the RAG engine singleton."""
    global rag_engine
    if rag_engine is None:
        print("Initializing RAG Engine...")
        rag_engine = RAGEngine(gemini_api_key=GEMINI_API_KEY)
    return rag_engine


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str
    top_k: Optional[int] = 5


class QuestionResponse(BaseModel):
    """Response model for answers."""
    answer: str
    sources: List[dict]
    num_chunks_used: int


class UploadResponse(BaseModel):
    """Response model for file uploads."""
    status: str
    filename: str
    message: str
    chunks: Optional[int] = None
    pages: Optional[int] = None
    duplicate: Optional[bool] = None
    existing_filename: Optional[str] = None
    options: Optional[List[str]] = None
    hash: Optional[str] = None


class DuplicateActionRequest(BaseModel):
    """Request model for handling duplicate documents."""
    filename: str
    file_hash: str
    action: str  # "use_existing", "replace", "cancel"


class DocumentInfo(BaseModel):
    """Document information model."""
    doc_id: str
    filename: str
    hash: str
    upload_timestamp: str
    num_chunks: int
    num_pages: int


class StatsResponse(BaseModel):
    """System statistics response."""
    total_documents: int
    total_chunks: int
    index_size: int
    embedding_model: str
    embedding_dimension: int


class DeleteResponse(BaseModel):
    """Delete document response."""
    status: str
    message: str


# ============================================
# STARTUP EVENT
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize RAG engine on startup."""
    print("Starting Multi-PDF RAG System...")
    get_rag_engine()
    print("RAG System ready!")


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Multi-PDF RAG System is running",
        "version": "1.0.0"
    }


@app.get("/ping")
async def ping():
    """Lightweight ping endpoint for quick connectivity checks."""
    return {"ok": True}


@app.get("/health")
async def health_check():
    """Detailed health check."""
    engine = get_rag_engine()
    stats = engine.get_stats()
    return {
        "status": "healthy",
        **stats
    }


@app.post("/upload-pdfs", response_model=List[UploadResponse])
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload multiple PDF files.
    
    - Accepts multiple PDF uploads
    - Detects duplicates via SHA-256 hash
    - Returns duplicate warnings with options
    - Processes and embeds new documents
    """
    engine = get_rag_engine()
    results = []
    
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            results.append(UploadResponse(
                status="error",
                filename=file.filename,
                message="Only PDF files are allowed"
            ))
            continue
        
        try:
            # Read file content
            content = await file.read()
            
            # Process document
            result = engine.upload_document(
                filename=file.filename,
                file_content=content,
                action="auto"
            )
            
            # Convert to response model
            if result["status"] == "duplicate":
                results.append(UploadResponse(
                    status="duplicate",
                    filename=result["filename"],
                    message=result["message"],
                    duplicate=True,
                    existing_filename=result.get("existing_filename"),
                    options=result.get("options"),
                    hash=result.get("hash")
                ))
            else:
                results.append(UploadResponse(
                    status=result["status"],
                    filename=result["filename"],
                    message=result["message"],
                    chunks=result.get("chunks"),
                    pages=result.get("pages"),
                    duplicate=False
                ))
                
        except Exception as e:
            results.append(UploadResponse(
                status="error",
                filename=file.filename,
                message=f"Error processing file: {str(e)}"
            ))
    
    return results


@app.post("/handle-duplicate", response_model=UploadResponse)
async def handle_duplicate(
    file: UploadFile = File(...),
    action: str = Form(...)
):
    """
    Handle duplicate document with user's chosen action.
    
    Actions:
    - use_existing: Reuse existing embeddings
    - replace: Re-process and update embeddings
    - cancel: Cancel the upload
    """
    if action not in ["use_existing", "replace", "cancel"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid action. Must be 'use_existing', 'replace', or 'cancel'"
        )
    
    engine = get_rag_engine()
    
    try:
        content = await file.read()
        result = engine.upload_document(
            filename=file.filename,
            file_content=content,
            action=action
        )
        
        return UploadResponse(
            status=result["status"],
            filename=result["filename"],
            message=result["message"],
            chunks=result.get("chunks"),
            pages=result.get("pages"),
            duplicate=result.get("reused", False)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error handling duplicate: {str(e)}"
        )


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about uploaded documents.
    
    - Embeds the user question
    - Retrieves top-k relevant chunks
    - Generates answer using Gemini with retrieved context
    - Returns answer with source citations
    """
    engine = get_rag_engine()
    
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    # Check if any documents are uploaded
    if engine.get_stats()["total_documents"] == 0:
        return QuestionResponse(
            answer="No documents have been uploaded yet. Please upload PDF documents first.",
            sources=[],
            num_chunks_used=0
        )
    
    try:
        result = engine.ask(
            query=request.question,
            top_k=request.top_k or 5
        )
        
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            num_chunks_used=result["num_chunks_used"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )


@app.get("/documents", response_model=List[DocumentInfo])
async def get_documents():
    """
    Get list of all uploaded documents.
    
    Returns document registry with:
    - Document ID
    - Original filename
    - Upload timestamp
    - File hash
    - Number of chunks
    - Number of pages
    """
    engine = get_rag_engine()
    documents = engine.get_all_documents()
    
    return [
        DocumentInfo(
            doc_id=doc["doc_id"],
            filename=doc["filename"],
            hash=doc["hash"],
            upload_timestamp=doc["upload_timestamp"],
            num_chunks=doc["num_chunks"],
            num_pages=doc["num_pages"]
        )
        for doc in documents
    ]


@app.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str):
    """
    Delete a document and its embeddings.
    
    - Removes document from registry
    - Removes embeddings from FAISS index
    - Updates persistent storage
    """
    engine = get_rag_engine()
    result = engine.delete_document(doc_id)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )
    
    return DeleteResponse(
        status=result["status"],
        message=result["message"]
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics."""
    engine = get_rag_engine()
    stats = engine.get_stats()
    
    return StatsResponse(
        total_documents=stats["total_documents"],
        total_chunks=stats["total_chunks"],
        index_size=stats["index_size"],
        embedding_model=stats["embedding_model"],
        embedding_dimension=stats["embedding_dimension"]
    )


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
