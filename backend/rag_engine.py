"""
RAG Engine Module
=================
Handles all RAG pipeline operations:
- PDF text extraction
- Text chunking with overlap
- Embedding generation using SentenceTransformers
- FAISS vector storage and retrieval
- Metadata and document registry management
- Persistence of embeddings and metadata
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import PyPDF2
import google.generativeai as genai

# ============================================
# CONFIGURATION
# ============================================

# Paths for persistent storage
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
FAISS_INDEX_PATH = os.path.join(STORAGE_DIR, "faiss.index")
METADATA_PATH = os.path.join(STORAGE_DIR, "metadata.json")
DOCUMENTS_PATH = os.path.join(STORAGE_DIR, "documents.json")

# Chunking parameters
DEFAULT_CHUNK_SIZE = 200  # words per chunk
DEFAULT_OVERLAP_SIZE = 50  # overlapping words

# Retrieval parameters
DEFAULT_TOP_K = 5  # number of chunks to retrieve

# Embedding model
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # dimension of all-MiniLM-L6-v2 embeddings


class RAGEngine:
    """
    Main RAG Engine class that handles:
    - Document processing and embedding
    - FAISS index management
    - Query processing and answer generation
    - Persistence of all data
    """
    
    def __init__(self, gemini_api_key: str):
        """
        Initialize the RAG Engine.
        
        Args:
            gemini_api_key: API key for Google Gemini
        """
        # Ensure storage directory exists
        os.makedirs(STORAGE_DIR, exist_ok=True)
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        
        # Initialize Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Initialize or load FAISS index
        self.index: Optional[faiss.IndexFlatL2] = None
        self.metadata: List[Dict] = []  # Stores chunk text, source, page
        self.documents: Dict[str, Dict] = {}  # Document registry
        
        # Load existing data if available
        self._load_persistent_data()
        
        print(f"RAG Engine initialized. Documents: {len(self.documents)}, Chunks: {len(self.metadata)}")
    
    # ============================================
    # PERSISTENCE METHODS
    # ============================================
    
    def _load_persistent_data(self):
        """Load FAISS index, metadata, and document registry from disk."""
        
        # Load document registry
        if os.path.exists(DOCUMENTS_PATH):
            with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            print(f"Loaded {len(self.documents)} documents from registry")
        
        # Load metadata
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            print(f"Loaded {len(self.metadata)} chunks metadata")
        
        # Load FAISS index
        if os.path.exists(FAISS_INDEX_PATH) and len(self.metadata) > 0:
            self.index = faiss.read_index(FAISS_INDEX_PATH)
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
        else:
            # Create new empty index
            self.index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
            print("Created new FAISS index")
    
    def _save_persistent_data(self):
        """Save FAISS index, metadata, and document registry to disk."""
        
        # Save document registry
        with open(DOCUMENTS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, indent=2, ensure_ascii=False)
        
        # Save metadata
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        
        # Save FAISS index
        if self.index is not None and self.index.ntotal > 0:
            faiss.write_index(self.index, FAISS_INDEX_PATH)
        
        print("Persistent data saved successfully")
    
    # ============================================
    # DOCUMENT PROCESSING METHODS
    # ============================================
    
    @staticmethod
    def compute_file_hash(file_content: bytes) -> str:
        """
        Compute SHA-256 hash of file content.
        
        Args:
            file_content: Raw bytes of the file
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def chunk_text_with_overlap(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, 
                                 overlap_size: int = DEFAULT_OVERLAP_SIZE) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text to chunk
            chunk_size: Number of words per chunk
            overlap_size: Number of overlapping words between chunks
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        start = 0
        
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
            start += chunk_size - overlap_size
        
        return chunks
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> List[Dict]:
        """
        Extract text from PDF page by page.
        
        Args:
            pdf_content: Raw bytes of PDF file
            
        Returns:
            List of dicts with page_num and text
        """
        import io
        pages = []
        
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        "page_num": page_num + 1,
                        "text": text
                    })
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            raise
        
        return pages
    
    def process_pdf(self, filename: str, file_content: bytes, 
                    chunk_size: int = DEFAULT_CHUNK_SIZE,
                    overlap_size: int = DEFAULT_OVERLAP_SIZE) -> List[Dict]:
        """
        Process a PDF: extract text, chunk it, and prepare metadata.
        
        Args:
            filename: Original filename
            file_content: Raw bytes of PDF
            chunk_size: Words per chunk
            overlap_size: Overlap between chunks
            
        Returns:
            List of chunk metadata dicts
        """
        # Extract pages
        pages = self.extract_text_from_pdf(file_content)
        
        # Chunk each page
        chunks_metadata = []
        for page_info in pages:
            page_chunks = self.chunk_text_with_overlap(
                page_info["text"], 
                chunk_size, 
                overlap_size
            )
            for chunk_text in page_chunks:
                chunks_metadata.append({
                    "text": chunk_text,
                    "source": filename,
                    "page": page_info["page_num"]
                })
        
        return chunks_metadata
    
    # ============================================
    # DUPLICATE DETECTION METHODS
    # ============================================
    
    def check_duplicate(self, file_hash: str) -> Optional[Dict]:
        """
        Check if a document with the same hash already exists.
        
        Args:
            file_hash: SHA-256 hash of the file
            
        Returns:
            Document info if duplicate found, None otherwise
        """
        for doc_id, doc_info in self.documents.items():
            if doc_info.get("hash") == file_hash:
                return {"doc_id": doc_id, **doc_info}
        return None
    
    def get_document_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Get document info by filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Document info if found, None otherwise
        """
        for doc_id, doc_info in self.documents.items():
            if doc_info.get("filename") == filename:
                return {"doc_id": doc_id, **doc_info}
        return None
    
    # ============================================
    # EMBEDDING AND INDEXING METHODS
    # ============================================
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        embeddings = self.embed_model.encode(texts)
        return np.array(embeddings).astype("float32")
    
    def add_to_index(self, chunks_metadata: List[Dict]) -> int:
        """
        Add new chunks to FAISS index and metadata.
        
        Args:
            chunks_metadata: List of chunk dicts with text, source, page
            
        Returns:
            Number of chunks added
        """
        if not chunks_metadata:
            return 0
        
        # Extract texts for embedding
        texts = [c["text"] for c in chunks_metadata]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Add to metadata
        self.metadata.extend(chunks_metadata)
        
        return len(chunks_metadata)
    
    def remove_document_from_index(self, filename: str):
        """
        Remove all chunks of a document from the index.
        Note: FAISS IndexFlatL2 doesn't support removal, so we rebuild.
        
        Args:
            filename: Filename of document to remove
        """
        # Filter out chunks from this document
        remaining_metadata = [
            m for m in self.metadata if m["source"] != filename
        ]
        
        if len(remaining_metadata) == len(self.metadata):
            return  # Nothing to remove
        
        # Rebuild index with remaining chunks
        self.metadata = remaining_metadata
        
        if self.metadata:
            texts = [m["text"] for m in self.metadata]
            embeddings = self.generate_embeddings(texts)
            self.index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
            self.index.add(embeddings)
        else:
            self.index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
        
        print(f"Removed document '{filename}' from index")
    
    # ============================================
    # DOCUMENT UPLOAD METHODS
    # ============================================
    
    def upload_document(self, filename: str, file_content: bytes, 
                        action: str = "auto") -> Dict:
        """
        Upload and process a document.
        
        Args:
            filename: Original filename
            file_content: Raw bytes of PDF
            action: "auto", "use_existing", "replace", or "cancel"
            
        Returns:
            Result dict with status and info
        """
        # Compute hash
        file_hash = self.compute_file_hash(file_content)
        
        # Check for duplicate
        existing_doc = self.check_duplicate(file_hash)
        
        if existing_doc:
            if action == "auto":
                # Return duplicate warning
                return {
                    "status": "duplicate",
                    "filename": filename,
                    "existing_filename": existing_doc["filename"],
                    "hash": file_hash,
                    "message": f"Document already exists as '{existing_doc['filename']}'",
                    "options": ["use_existing", "replace", "cancel"]
                }
            elif action == "use_existing":
                return {
                    "status": "success",
                    "filename": existing_doc["filename"],
                    "message": "Using existing document embeddings",
                    "chunks": 0,
                    "reused": True
                }
            elif action == "cancel":
                return {
                    "status": "cancelled",
                    "filename": filename,
                    "message": "Upload cancelled"
                }
            elif action == "replace":
                # Remove old document and continue with upload
                self.remove_document_from_index(existing_doc["filename"])
                del self.documents[existing_doc["doc_id"]]
        
        # Process new document
        try:
            chunks_metadata = self.process_pdf(filename, file_content)
            
            if not chunks_metadata:
                return {
                    "status": "error",
                    "filename": filename,
                    "message": "No text could be extracted from PDF"
                }
            
            # Add to index
            num_chunks = self.add_to_index(chunks_metadata)
            
            # Register document
            doc_id = f"doc_{len(self.documents) + 1}_{int(datetime.now().timestamp())}"
            self.documents[doc_id] = {
                "filename": filename,
                "hash": file_hash,
                "upload_timestamp": datetime.now().isoformat(),
                "num_chunks": num_chunks,
                "num_pages": max(c["page"] for c in chunks_metadata)
            }
            
            # Persist changes
            self._save_persistent_data()
            
            return {
                "status": "success",
                "filename": filename,
                "message": f"Document processed successfully",
                "chunks": num_chunks,
                "pages": self.documents[doc_id]["num_pages"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "filename": filename,
                "message": f"Error processing document: {str(e)}"
            }
    
    # ============================================
    # QUERY AND RETRIEVAL METHODS
    # ============================================
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict]:
        """
        Retrieve most relevant chunks for a query.
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks with metadata
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Limit top_k to available chunks
        top_k = min(top_k, self.index.ntotal)
        
        # Embed query
        query_embedding = self.embed_model.encode([query]).astype("float32")
        
        # Search FAISS
        distances, indices = self.index.search(query_embedding, k=top_k)
        
        # Gather results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                results.append({
                    **self.metadata[idx],
                    "distance": float(distances[0][i]),
                    "relevance_rank": i + 1
                })
        
        return results
    
    def generate_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Generate answer using Gemini with retrieved context.
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant chunks
            
        Returns:
            Generated answer string
        """
        if not context_chunks:
            return "I don't have enough information to answer this question. Please upload relevant documents first."
        
        # Build context string
        context_parts = []
        for chunk in context_chunks:
            context_parts.append(
                f"[Source: {chunk['source']}, Page {chunk['page']}]\n{chunk['text']}"
            )
        context = "\n\n".join(context_parts)
        
        # Create prompt
        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context.
Do NOT make up information that is not in the context.
If the context doesn't contain enough information to answer, say so clearly.
You may summarize, combine, or rephrase information from the context to make your answer clear and helpful.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def ask(self, query: str, top_k: int = DEFAULT_TOP_K) -> Dict:
        """
        Main query method: retrieve context and generate answer.
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            
        Returns:
            Dict with answer and sources
        """
        # Retrieve relevant chunks
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k)
        
        # Generate answer
        answer = self.generate_answer(query, relevant_chunks)
        
        # Format sources (unique)
        sources = []
        seen = set()
        for chunk in relevant_chunks:
            source_key = f"{chunk['source']}_{chunk['page']}"
            if source_key not in seen:
                sources.append({
                    "file": chunk["source"],
                    "page": chunk["page"]
                })
                seen.add(source_key)
        
        return {
            "answer": answer,
            "sources": sources,
            "num_chunks_used": len(relevant_chunks)
        }
    
    # ============================================
    # DOCUMENT MANAGEMENT METHODS
    # ============================================
    
    def get_all_documents(self) -> List[Dict]:
        """
        Get list of all uploaded documents.
        
        Returns:
            List of document info dicts
        """
        return [
            {"doc_id": doc_id, **info}
            for doc_id, info in self.documents.items()
        ]
    
    def delete_document(self, doc_id: str) -> Dict:
        """
        Delete a document and its embeddings.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            Result dict
        """
        if doc_id not in self.documents:
            return {
                "status": "error",
                "message": f"Document {doc_id} not found"
            }
        
        filename = self.documents[doc_id]["filename"]
        
        # Remove from index
        self.remove_document_from_index(filename)
        
        # Remove from registry
        del self.documents[doc_id]
        
        # Persist changes
        self._save_persistent_data()
        
        return {
            "status": "success",
            "message": f"Document '{filename}' deleted successfully"
        }
    
    def get_stats(self) -> Dict:
        """
        Get system statistics.
        
        Returns:
            Dict with stats
        """
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.metadata),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedding_dimension": EMBEDDING_DIMENSION
        }
