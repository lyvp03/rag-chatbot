# RAG App — Backend

FastAPI backend for the RAG (Retrieval-Augmented Generation) application.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 4. Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```


.venv\Scripts\activate


## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |
| POST | `/api/documents/upload` | Upload a document |
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}/status` | Get document processing status |
| DELETE | `/api/documents/{id}` | Delete a document |
| POST | `/api/chat` | Chat with streaming SSE response |

## Supported File Types

- **Text**: PDF, TXT, MD
- **Audio**: MP3, WAV, M4A, WEBM (transcribed via Whisper)
