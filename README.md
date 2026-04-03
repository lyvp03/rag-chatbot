# Full-Stack RAG (Retrieval-Augmented Generation) Application

This is a comprehensive Full-Stack RAG application that enables users to upload various document formats (text and audio) and leverage the capabilities of Large Language Models (LLMs) to perform semantic searches and interactive conversations based on the uploaded content.

## Key Features

- **Frontend**: Built with Next.js (App Router), TypeScript, and Tailwind CSS. It provides a robust and intuitive user interface tailored for document management and real-time chat interactions.
- **Backend**: Developed utilizing FastAPI (Python), delivering a high-performance, fully asynchronous API architecture.
- **Multi-Format Support**:
  - **Text**: Seamless processing of PDF, TXT, and Markdown (MD) files.
  - **Audio**: Integration with OpenAI Whisper for automated transcription of MP3, WAV, and M4A audio files.
- **Vector Database**: Implements FAISS (Facebook AI Similarity Search) to ensure highly efficient storage, indexing, and semantic retrieval of embedded data.
- **Streamlined Chat Experience**: Server-Sent Events (SSE) implementation to return responses as a continuous stream, delivering a ChatGPT-like interaction using OpenAI models.
- **Dockerized Environment**: Fully containerized using Docker and Docker Compose, facilitating a seamless, single-command deployment process.

---

## Project Architecture

The repository is modularized into two distinct parent directories:

```
rag-app/
├── backend/          # FastAPI server
│   ├── app/          # Core source code
│   ├── faiss_data/   # Persistent storage for Vector Database Index
│   ├── uploads/      # Persistent storage for user-uploaded files
│   └── Dockerfile
├── frontend/         # Next.js web application
│   ├── src/app/      # Core source code (App Router)
│   └── Dockerfile
└── docker-compose.yml
```

---

## Setup and Execution Guide

### Method 1: Deploying via Docker (Recommended)

Using Docker mitigates the need to independently configure Node.js, Python, or ffmpeg on the host machine.

**1. Configure Environment Variables**
Navigate to the `backend` directory, duplicate the environment template, and provide your valid API keys:
```bash
cp backend/.env.example backend/.env
# Add your configuration to backend/.env (e.g., OPENAI_API_KEY=sk-...)
```

**2. Initialize with Docker Compose**
From the root directory of the project, execute:
```bash
docker-compose up -d --build
```

**3. Access the Dispatched Services**
- **Frontend Application**: http://localhost:3000
- **Backend API Documentation**: http://localhost:8000/docs
- **Data Persistence**: FAISS indexing data and uploaded artifacts will securely persist within the `backend/faiss_data` and `backend/uploads` local directories.

---

### Method 2: Manual Local Execution (Development Mode)

If you require direct environment execution for active development, adhere to the following setup parameters.

#### Prerequisites
- **Python >= 3.11**
- **Node.js >= 20**
- Installation of **ffmpeg** on the system PATH (essential for audio processing).

#### Step 1: Initialize the Backend
```bash
cd backend

# Establish a virtual programming environment
python -m venv .venv
.venv\Scripts\activate       # For Windows
# source .venv/bin/activate  # For macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Specify environment variable parameters
cp .env.example .env

# Start the application server
fastapi dev app/main.py
```
*The Backend API will populate at http://localhost:8000*

#### Step 2: Initialize the Frontend
(Execute this within a newly spawned terminal instance)
```bash
cd frontend

# Install external modules
npm install

# (Optional) specific local environment overrides
cp .env.local.example .env.local

# Start the development server
npm run dev
```
*The Frontend Application will populate at http://localhost:3000*

---

## References

- Comprehensive API endpoint parameters: [`API_DOCS.md`](./API_DOCS.md)
- In-depth architectural structure breakdown: [`project_structure.md`](./project_structure.md)
