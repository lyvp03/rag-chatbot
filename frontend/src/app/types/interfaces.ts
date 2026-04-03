// ─── Types ────────────────────────────────────────────────────────────────────
 
export type DocumentStatus = "pending" | "processing" | "completed" | "failed";
 
export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  chunk_count: number;
  uploaded_at: string;
  error_message: string | null;
}
 
export interface UploadResponse {
  id: string;
  filename: string;
  status: DocumentStatus;
  message: string;
}
 
export interface HealthResponse {
  status: string;
  version: string;
  vector_database_collection: string;
  document_count: number;
  timestamp: string;
}
 
export interface SourceChunk {
  filename: string;
  file_type: string;
  chunk_index: number;
  content_preview: string;
  relevance_score: number;
}
 
export interface ChatStreamCallbacks {
  onSources?: (sources: SourceChunk[]) => void;
  onToken?: (token: string) => void;
  onDone?: () => void;
  onError?: (error: string) => void;
}