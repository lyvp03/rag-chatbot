# RAG API Documentation

Tài liệu này mô tả các API endpoints của Backend FastAPI để frontend có thể dễ dàng gọi và tích hợp.

**Base URL**: `http://localhost:8000/api` (Mặc định khi chạy local)

---

## 1. Trạng thái hệ thống (Health)

### 1.1. Health Check
Kiểm tra xem server và database vector (ChromaDB) có đang hoạt động hay không.
- **Phương thức:** `GET`
- **Endpoint:** `/health`
- **Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "vector_database_collection": "rag_documents",
  "document_count": 125,
  "timestamp": "2026-04-02T13:40:00.000Z"
}
```

---

## 2. Quản lý Tài liệu (Documents)

### 2.1. Tải lên tài liệu
Upload một file tài liệu hoặc audio để AI xử lý và đưa vào vector database. Quá trình xử lý chunk và index sẽ được đưa vào chạy ngầm (background task).
- **Phương thức:** `POST`
- **Endpoint:** `/documents/upload`
- **Content-Type**: `multipart/form-data`
- **Body:**
  - `file`: File cần upload (Hỗ trợ: `pdf`, `txt`, `md`, `mp3`, `wav`, `m4a`, `webm`)
- **Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "document.pdf",
  "status": "pending",
  "message": "Document uploaded and queued for processing"
}
```

### 2.2. Lấy danh sách tài liệu
Lấy danh sách tất cả các tài liệu đã upload, bao gồm trạng thái xử lý hiện tại và số lượng chunk tạo ra.
- **Phương thức:** `GET`
- **Endpoint:** `/documents`
- **Response:** `200 OK`
```json
{
  "documents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "document.pdf",
      "file_type": "pdf",
      "file_size_bytes": 1024500,
      "status": "completed",
      "chunk_count": 45,
      "uploaded_at": "1680415200.0",
      "error_message": null
    }
  ],
  "total": 1
}
```
*Lưu ý về các giá trị của trạng thái (`status`):* `pending`, `processing`, `completed`, `failed`

### 2.3. Lấy trạng thái xử lý một tài liệu
Kiểm tra xem việc xử lý (chunk và index) của một tài liệu cụ thể đã xong chưa.
- **Phương thức:** `GET`
- **Endpoint:** `/documents/{doc_id}/status`
- **Path Parameter**:
  - `doc_id`: ID của tài liệu do API trả về ở bước upload
- **Response:** `200 OK` (Trả về object tương tự phần tử trong danh sách `documents`).

### 2.4. Xóa tài liệu
Xóa file đã upload và tất cả các chunk text có trong vector DB liên quan đến file đó.
- **Phương thức:** `DELETE`
- **Endpoint:** `/documents/{doc_id}`
- **Path Parameter**:
  - `doc_id`: ID của tài liệu.
- **Response:** `200 OK`
```json
{
  "message": "Document deleted. 45 chunks removed."
}
```

---

## 3. Chat (RAG AI Agent)

### 3.1. Gửi câu hỏi (Streaming Response)
Nhận câu trả lời từ AI theo dạng luồng dữ liệu (Stream/SSE). 
- **Phương thức:** `POST`
- **Endpoint:** `/chat`
- **Content-Type**: `application/json`
- **Accept**: `text/event-stream`
- **Body:**
```json
{
  "message": "Nội dung người dùng hỏi",
  "top_k": 5
}
```
*Ghi chú:* `top_k` (tùy chọn, mặc định 5): Số tài liệu liên quan tối đa được truy xuất từ Vector DB.

**Response (Server-Sent Events - SSE):**
Trạng thái HTTP: `200 OK`, định dạng luồng dữ liệu liên tục:
Mỗi event stream có kiểu được chỉ định ở field `event:`.

**Cấu trúc dữ kiện trả về:**

1. **Sự kiện `sources` (Được gửi đầu tiên)**
   Chứa thông tin các trích đoạn văn bản dùng để tạo nên câu trả lời.
   ```text
   event: sources
   data: [{"filename": "doc.pdf", "file_type": "pdf", "chunk_index": 0, "content_preview": "...", "relevance_score": 0.98}]
   ```
2. **Sự kiện `token` (Gửi liên tục)**
   Mỗi mảnh ký tự của một câu được gen ra bởi LLM.
   ```text
   event: token
   data: Chào
   
   event: token
   data:  bạn!
   ```
3. **Sự kiện `done` (Kết thúc)**
   Báo hiệu stream AI trả lời đã xong.
   ```text
   event: done
   data: [DONE]
   ```
4. **Sự kiện `error` (Gặp lỗi)**
   Báo lỗi khi gửi/xử lý chat.
   ```text
   event: error
   data: {"detail": "Error generating response"}
   ```

**Cách gọi cơ bản phía Frontend bằng Fetch API cho SSE / POST:**
Frontend có thể lấy dữ liệu Stream bằng hàm hỗ trợ cho fetch (như thay vì `EventSource` truyền thống thì đọc byte từ `response.body.getReader()`) hoặc dùng thư viện (vd `@microsoft/fetch-event-source`).
