"""
FastAPI Backend for Multi-PDF RAG System
=========================================
Production-ready API for:
- Multiple PDF uploads with duplicate detection
- Question answering using RAG pipeline
- Document management
"""

import os
import asyncio
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

# ============================================
# RAG ENGINE WRAPPER (Non-blocking initialization)
# ============================================

class RAGEngineWrapper:
    """Wrapper that initializes RAGEngine in background without blocking the event loop."""
    
    def __init__(self):
        self.engine: Optional[RAGEngine] = None
        self.ready: bool = False
        self._init_task: Optional[asyncio.Task] = None
        self._init_error: Optional[Exception] = None

    async def start_background_init(self, gemini_api_key: str):
        """Start initializing the heavy RAGEngine in a background thread."""
        if self._init_task is None:
            print("Starting RAG Engine initialization in background...")
            self._init_task = asyncio.create_task(self._init_in_thread(gemini_api_key))

    async def _init_in_thread(self, gemini_api_key: str):
        """Run the blocking RAGEngine constructor in a worker thread."""
        try:
            # Move the heavy synchronous initialization off the main event loop
            self.engine = await asyncio.to_thread(RAGEngine, gemini_api_key=gemini_api_key)
            self.ready = True
            print("✓ RAG Engine initialized successfully (background)")
        except Exception as e:
            self._init_error = e
            self.ready = False
            print(f"✗ RAG Engine initialization failed: {e}")


# Global wrapper instance
RAG = RAGEngineWrapper()


def get_rag_engine() -> RAGEngine:
    """Return the engine if ready; otherwise raise RuntimeError.
    
    Note: Endpoints should check RAG.ready and return 503 while initializing.
    """
    if RAG.engine is None:
        raise RuntimeError("RAG engine not initialized yet")
    return RAG.engine


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
    """Start RAG engine initialization in background - server becomes responsive immediately."""
    print("Starting Multi-PDF RAG System...")
    await RAG.start_background_init(gemini_api_key=GEMINI_API_KEY)
    print("Server ready! (RAG engine loading in background)")


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
    """Detailed health check - remains responsive even while engine loads."""
    if RAG.ready and RAG.engine is not None:
        try:
            stats = await asyncio.to_thread(RAG.engine.get_stats)
            return {"status": "healthy", **stats}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    elif RAG._init_error:
        return {"status": "error", "message": f"Initialization failed: {RAG._init_error}"}
    else:
        return {"status": "initializing", "message": "RAG engine is loading in background"}


@app.post("/upload-pdfs", response_model=List[UploadResponse])
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload multiple PDF files.
    
    - Accepts multiple PDF uploads
    - Detects duplicates via SHA-256 hash
    - Returns duplicate warnings with options
    - Processes and embeds new documents
    """
    if not RAG.ready or RAG.engine is None:
        raise HTTPException(status_code=503, detail="Engine is initializing, please try again in a moment")
    
    engine = RAG.engine
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
            
            # Process document (run in thread to avoid blocking)
            result = await asyncio.to_thread(
                engine.upload_document,
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
    
    if not RAG.ready or RAG.engine is None:
        raise HTTPException(status_code=503, detail="Engine is initializing, please try again in a moment")
    
    engine = RAG.engine
    
    try:
        content = await file.read()
        result = await asyncio.to_thread(
            engine.upload_document,
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
    if not RAG.ready or RAG.engine is None:
        raise HTTPException(status_code=503, detail="Engine is initializing, please try again in a moment")
    
    engine = RAG.engine
    
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    # Check if any documents are uploaded
    stats = await asyncio.to_thread(engine.get_stats)
    if stats["total_documents"] == 0:
        return QuestionResponse(
            answer="No documents have been uploaded yet. Please upload PDF documents first.",
            sources=[],
            num_chunks_used=0
        )
    
    try:
        result = await asyncio.to_thread(
            engine.ask,
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
    if not RAG.ready or RAG.engine is None:
        raise HTTPException(status_code=503, detail="Engine is initializing, please try again in a moment")
    
    engine = RAG.engine
    documents = await asyncio.to_thread(engine.get_all_documents)
    
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
    if not RAG.ready or RAG.engine is None:
        raise HTTPException(status_code=503, detail="Engine is initializing, please try again in a moment")
    
    engine = RAG.engine
    result = await asyncio.to_thread(engine.delete_document, doc_id)
    
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
    if not RAG.ready or RAG.engine is None:
        raise HTTPException(status_code=503, detail="Engine is initializing, please try again in a moment")
    
    engine = RAG.engine
    stats = await asyncio.to_thread(engine.get_stats)
    
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
