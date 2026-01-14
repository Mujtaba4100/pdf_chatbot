# 🔍 Multi-PDF RAG System

A production-ready, full-stack Retrieval-Augmented Generation (RAG) application that allows users to upload multiple PDFs and query them using AI. The system features **persistent embeddings** so documents are processed once and never need re-embedding on restart.

![RAG System](https://img.shields.io/badge/RAG-System-blue) ![Python](https://img.shields.io/badge/Python-3.10+-green) ![React](https://img.shields.io/badge/React-19-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal)

---

## 📋 Table of Contents

- [What is RAG?](#-what-is-rag)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [How It Works](#-how-it-works)
- [Persistence Mechanism](#-persistence-mechanism)
- [Duplicate Handling](#-duplicate-handling)

---

## 🧠 What is RAG?

**Retrieval-Augmented Generation (RAG)** is an AI architecture that enhances Large Language Models (LLMs) by providing them with relevant context retrieved from a knowledge base before generating responses.

### Traditional LLM vs RAG

| Traditional LLM | RAG System |
|----------------|------------|
| Relies on training data only | Retrieves relevant documents at query time |
| May hallucinate facts | Grounds answers in actual documents |
| Static knowledge | Dynamic, updatable knowledge base |
| Generic responses | Context-specific, accurate answers |

### RAG Pipeline Steps

1. **Document Ingestion**: Upload PDFs → Extract text → Chunk into smaller pieces
2. **Embedding Generation**: Convert text chunks into numerical vectors using SentenceTransformers
3. **Vector Storage**: Store embeddings in FAISS for fast similarity search
4. **Query Processing**: Embed user question → Find similar chunks → Retrieve context
5. **Answer Generation**: Send context + question to LLM (Gemini) → Generate grounded answer

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        REACT FRONTEND                           │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │PDF Upload│  │Document List │  │Question/Answer Panel  │   │
│  └────┬─────┘  └──────┬───────┘  └───────────┬────────────┘   │
└───────┼───────────────┼──────────────────────┼─────────────────┘
        │               │                      │
        ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐    │
│  │/upload-pdfs│  │/documents  │  │/ask                    │    │
│  └─────┬──────┘  └─────┬──────┘  └───────────┬────────────┘    │
└────────┼───────────────┼─────────────────────┼─────────────────┘
         │               │                     │
         ▼               ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RAG ENGINE                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ SentenceTransformers │ FAISS Index │ Gemini API            │ │
│  │ (all-MiniLM-L6-v2)   │ (Vector DB) │ (Text Generation)     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENT STORAGE                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │ faiss.index  │  │ metadata.json│  │ documents.json   │      │
│  │ (Embeddings) │  │ (Chunk data) │  │ (Doc registry)   │      │
│  └──────────────┘  └──────────────┘  └──────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Backend Features
- ✅ Multiple PDF upload processing
- ✅ Page-wise text extraction with PyPDF2
- ✅ **OCR support for extracting text from images in PDFs** (Tesseract)
- ✅ Text chunking with configurable overlap
- ✅ Embedding generation using all-MiniLM-L6-v2
- ✅ FAISS vector storage for fast similarity search
- ✅ Persistent storage (survives restarts)
- ✅ Duplicate detection via SHA-256 hashing
- ✅ Document registry management
- ✅ Context-grounded answer generation with Gemini
- ✅ **Smart source verification - only cites chunks that support the answer**
- ✅ Source citations with file and page numbers

### Frontend Features
- ✅ Drag-and-drop PDF upload
- ✅ Multiple file selection
- ✅ **Progressive disclosure UI - clean, focused interface**
- ✅ Uploaded documents list with metadata
- ✅ Duplicate document warning modal
- ✅ Question input with loading states
- ✅ Answer display with source citations
- ✅ System statistics panel
- ✅ Toast notifications
- ✅ Responsive design

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core language |
| **FastAPI** | REST API framework |
| **FAISS** | Vector similarity search |
| **SentenceTransformers** | Text embeddings |
| **Google Gemini** | LLM for answer generation |
| **PyPDF2** | PDF text extraction |
| **Tesseract OCR** | Extract text from images |
| **Pillow** | Image processing |
| **Pydantic** | Data validation |
| **Uvicorn** | ASGI server |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 19** | UI framework |
| **Vite** | Build tool |
| **Plain CSS** | Styling |

---

## 📁 Project Structure

```
pdf_chatbot/
│
├── backend/
│   ├── main.py              # FastAPI application & endpoints
│   ├── rag_engine.py        # Core RAG pipeline logic
│   ├── requirements.txt     # Python dependencies
│   └── storage/
│       ├── faiss.index      # Persisted FAISS embeddings
│       ├── metadata.json    # Chunk text & source info
│       └── documents.json   # Document registry
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── App.css              # Application styles
│   │   ├── index.css            # Global styles
│   │   ├── main.jsx             # React entry point
│   │   ├── components/
│   │   │   ├── PDFUpload.jsx    # File upload component
│   │   │   ├── DocumentList.jsx # Document display component
│   │   │   ├── QuestionAnswer.jsx # Q&A interface
│   │   │   ├── DuplicateModal.jsx # Duplicate handling modal
│   │   │   ├── StatsPanel.jsx   # Statistics display
│   │   │   └── Toast.jsx        # Notification component
│   │   └── services/
│   │       └── api.js           # API communication service
│   ├── public/              # Static assets
│   ├── index.html           # HTML entry point
│   ├── package.json         # Node.js dependencies
│   ├── vite.config.js       # Vite configuration
│   └── eslint.config.js     # ESLint configuration
│
└── README.md                # This file
```

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm or yarn
- **Tesseract OCR** (for image text extraction - see [OCR Setup Guide](OCR_SETUP.md))

### 1. Clone/Navigate to Project

```bash
cd "e:\AI DMS\pdf_chatbot"
```

### 2. Backend Setup

```bash
# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
cd backend
pip install -r requirements.txt
```

### 3. OCR Setup (Optional but Recommended)

To enable text extraction from images in PDFs:

**Quick Setup (Windows):**
```powershell
# Run the automated setup script
.\install_ocr.ps1
```

**Manual Setup:**
See [OCR_SETUP.md](OCR_SETUP.md) for detailed instructions.

**Note:** The system works without OCR but will skip image text extraction. If Tesseract is not installed, you'll see a warning message, but regular PDF text extraction continues normally.

### 4. Frontend Setup

```bash
# From project root, navigate to frontend folder
cd frontend
npm install
```

### 5. Configure API Key (Optional)

The Gemini API key is pre-configured. To use your own:

1. Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set environment variable:
   ```bash
   # Windows
   set GEMINI_API_KEY=your_api_key_here
   
   # macOS/Linux
   export GEMINI_API_KEY=your_api_key_here
   ```

---

## ▶️ Running the Application

### Start Backend Server

```bash
# From backend directory
cd backend
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend runs at: `http://localhost:8000`

### Start Frontend Development Server

```bash
# From frontend directory (new terminal)
cd frontend
npm run dev
```

The frontend runs at: `http://localhost:5173`

### Access the Application

Open your browser and navigate to: `http://localhost:5173`

---

## 📡 API Documentation

### Endpoints

#### `POST /upload-pdfs`
Upload multiple PDF files.

**Request:** `multipart/form-data` with files

**Response:**
```json
[
  {
    "status": "success",
    "filename": "document.pdf",
    "message": "Document processed successfully",
    "chunks": 45,
    "pages": 10
  }
]
```

#### `POST /ask`
Ask a question about uploaded documents.

**Request:**
```json
{
  "question": "What is machine learning?",
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "Machine learning is a subset of AI...",
  "sources": [
    {"file": "AI_DMS.pdf", "page": 3},
    {"file": "ML_Guide.pdf", "page": 7}
  ],
  "num_chunks_used": 5
}
```

#### `GET /documents`
Get list of all uploaded documents.

**Response:**
```json
[
  {
    "doc_id": "doc_1_1640000000",
    "filename": "AI_DMS.pdf",
    "hash": "sha256...",
    "upload_timestamp": "2026-01-01T12:00:00",
    "num_chunks": 45,
    "num_pages": 10
  }
]
```

#### `DELETE /documents/{doc_id}`
Delete a document and its embeddings.

#### `GET /stats`
Get system statistics.

#### `GET /health`
Health check endpoint.

---

## 🔄 How It Works

### Document Upload Flow

```
PDF File → Extract Text (Page-wise) → Chunk Text (200 words, 50 overlap)
    → Generate Embeddings (all-MiniLM-L6-v2) → Store in FAISS
    → Save metadata (text, source, page) → Update document registry
```

### Query Flow

```
User Question → Generate Embedding → FAISS Similarity Search
    → Retrieve Top-K Chunks → Build Context → Send to Gemini
    → Generate Grounded Answer → Return with Sources
```

---

## 💾 Persistence Mechanism

The system uses three persistent files:

### 1. `faiss.index`
- Binary file containing all document embeddings
- Loaded automatically on startup
- Uses FAISS's native serialization

### 2. `metadata.json`
- JSON file with chunk information:
  ```json
  [
    {
      "text": "chunk text content...",
      "source": "document.pdf",
      "page": 1
    }
  ]
  ```

### 3. `documents.json`
- Document registry:
  ```json
  {
    "doc_1_1640000000": {
      "filename": "document.pdf",
      "hash": "sha256...",
      "upload_timestamp": "2026-01-01T12:00:00",
      "num_chunks": 45,
      "num_pages": 10
    }
  }
  ```

### On Application Restart

1. Checks for existing storage files
2. Loads FAISS index with embeddings
3. Loads metadata and document registry
4. **NO re-embedding** - documents are immediately queryable

---

## 🔄 Duplicate Handling

When uploading a PDF, the system:

1. **Computes SHA-256 hash** of file content
2. **Checks against document registry**
3. If duplicate found, presents options:
   - **Use Existing**: Reuse existing embeddings (no processing)
   - **Replace**: Re-process document, update embeddings
   - **Cancel**: Abort upload

This ensures:
- No unnecessary reprocessing
- Clear user control over duplicates
- Efficient storage usage

---

## 🎯 Key Design Decisions

### Why No LangChain?
- **Simplicity**: Direct API calls are easier to debug
- **Performance**: Less abstraction overhead
- **Control**: Full visibility into the RAG pipeline
- **Learning**: Better understanding of how RAG works

### Why FAISS?
- **Speed**: Highly optimized for similarity search
- **Persistence**: Native save/load functionality
- **Scalability**: Handles millions of vectors efficiently
- **Simplicity**: Easy to use for L2 distance search

### Why SentenceTransformers?
- **Quality**: all-MiniLM-L6-v2 provides excellent embeddings
- **Speed**: Fast encoding even on CPU
- **Size**: Compact model (80MB)
- **No API costs**: Runs locally

---

## 🔒 Security Notes

- API keys should be stored in environment variables for production
- The frontend never exposes embeddings or API keys
- All PDF processing happens server-side
- CORS is configured for local development

---

## 🐛 Troubleshooting

### Backend won't start
- Ensure Python 3.10+ is installed
- Activate virtual environment
- Install all dependencies: `pip install -r requirements.txt`

### Frontend can't connect to backend
- Check backend is running on port 8000
- Verify CORS settings in `main.py`
- Check browser console for errors

### Embedding model download
- First run downloads the model (~80MB)
- Ensure internet connection for first startup
- Model is cached for subsequent runs

---

## 📝 License

This project is for educational purposes.

---

## 👨‍💻 Author

Built as a demonstration of production-ready RAG systems with persistent embeddings.

---

## 🙏 Acknowledgments

- [SentenceTransformers](https://www.sbert.net/) for embedding models
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Google Gemini](https://ai.google.dev/) for text generation
