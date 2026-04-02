# 🏗️ Kiến trúc ứng dụng RAG (Retrieval-Augmented Generation)

Ứng dụng RAG của bài toán được thiết kế theo mô hình **Client-Server** chuẩn, với Frontend React (Next.js) đảm nhiệm giao diện, và Backend Python (FastAPI) xử lý nghiệp vụ AI cốt lõi (Chunking, Embedding, Vector Search, LLM Chat).

---

## 🐍 1. Backend (FastAPI + LangChain + FAISS)
Nằm trong thư mục `backend/`

Thành phần này chịu trách nhiệm: (1) Nhận file tải lên, (2) Chia nhỏ và lưu vector bằng Embedding Model, (3) Tìm kiếm thông tin liên quan khi user hỏi, và (4) Gọi LLM (Chat completion) để trả lời.

```text
📁 backend/
├── 📄 requirements.txt     # Danh sách các thư viện Python (fastapi, langchain, faiss-cpu...)
├── 📄 .env                 # File chứa biến môi trường thực tế (API key, URL model)
├── 📄 .env.example         # File mẫu để biết cần các biến môi trường nào
│
└── 📁 app/                 # Chứa toàn bộ mã nguồn Backend
    ├── 📄 main.py          # Entrypoint của toàn bộ Backend. Nơi khởi tạo app FastAPI, cấu hình CORS, và nhúng các Routes.
    ├── 📄 config.py        # Định nghĩa các cấu hình hệ thống (Settings) bằng Pydantic. Lấy dữ liệu từ file .env.
    │
    ├── 📁 api/             # Chứa Controller/Router xử lý các HTTP API request
    │   ├── 📄 dependencies.py # Khởi tạo các Service (VectorDB, Chat) theo cơ chế Dependency Injection của FastAPI.
    │   └── 📁 routes/         
    │       ├── 📄 health.py   # API kiểm tra hệ thống còn sống hay lỗi (GET /api/health)
    │       ├── 📄 documents.py # API upload file, lấy lịch sử upload (POST /api/documents)
    │       └── 📄 chat.py     # API chat RAG, lấy câu hỏi của user để trả lời (POST /api/chat)
    │
    ├── 📁 core/            # (Tùy chọn) Chứa middleware bắt lỗi, config hệ thống riêng biệt
    │
    ├── 📁 models/          
    │   └── 📄 schemas.py   # Các pydantic Model định nghĩa Input/Output chuẩn của các API (VD: ChatRequest, DocumentResponse...)
    │
    └── 📁 services/        # Nơi chứa các thuật toán và logic nghiệp vụ chính (Business Logic)
        ├── 📄 vector_store.py      # Tương tác với FAISS Database. Có hàm add_chunk(), search_similarity()
        ├── 📄 document_processor.py# Chuyên xử lý file (.txt, .md, .pdf). Đọc file -> Tách đoạn nhỏ (Chunking) -> Đẩy vào Vector Store
        ├── 📄 audio_processor.py   # Chuyên biến đổi Audio (.mp3) thành Văn bản.
        └── 📄 chat_service.py      # Core RAG: Nhận câu hỏi -> Sinh vector câu hỏi -> Tìm trong VectorStore -> Gửi LLM -> Trả về kết quả.
```

---

## ⚛️ 2. Frontend (Next.js + TypeScript + Tailwind)
Nằm trong thư mục `frontend/`

```text
📁 frontend/
├── 📄 package.json         # Danh sách các thư viện Node.js (react, next, lucide-react...)
├── 📄 next.config.ts       # File cấu hình khi build Next.js
├── 📄 tsconfig.json        # Định nghĩa cấu hình TypeScript
│
└── 📁 src/                 # Mã nguồn giao diện chính
    └── 📁 app/             # App Router của Next.js (Phiên bản mới)
        ├── 📄 globals.css  # File CSS global, nạp Tailwind utilities
        ├── 📄 layout.tsx   # Khuôn giao diện chung của mọi màn hình (Header/Footer nằm đây nếu có)
        └── 📄 page.tsx     # Homepage. Cột File Upload bên trái, Cột Chat bằng AI bên phải. 
```

---

## 🔄 Dòng chảy Dữ liệu (Workflow)

Hai quy trình cốt lõi chạy trên cấu trúc này:

### 1️⃣ Quy trình Ingest Data (Đưa dữ liệu vào kho trí nhớ)
1. **Frontend**: Gửi `File` (PDF) lên API `POST /api/documents`.
2. **Backend Router** (`documents.py`): Nhận file, lưu tạm vào thư mục `./uploads/`.
3. **Backend Service** (`document_processor.py`): Tách PDF thành text, phân nhỏ ra (mỗi đoạn 500-1000 từ).
4. **Backend VectorDB** (`vector_store.py`): Gửi qua OpenAI API tạo dãy số nhúng (Embedding), lưu vào file nội bộ (FAISS vector base).

### 2️⃣ Quy trình Q&A Chat (Hỏi đáp với AI)
1. **Frontend**: Gửi Query `{"message": "Dự án này làm gì?"}` lên API `POST /api/chat`.
2. **Backend Router** (`chat.py`): Gọi sang `chat_service.py`.
3. **Service Xử lý** (`vector_store.py`): Chuyển câu hỏi sang vector -> So sánh (Similarity Search) với kho dữ liệu FAISS -> Trả về Top 5 đoạn văn bản khớp nhất.
4. **Service Trả Lời** (`chat_service.py`): Gom Câu hỏi + 5 đoạn văn bản liên quan nhét chung vào Prompt -> Gọi LLM API.
5. Cuối cùng, kết quả chữ được xuất ra Frontend.
