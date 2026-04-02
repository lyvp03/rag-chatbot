export interface NewsItem {
  id: number;
  type: string;
  guid: string;
  url: string;
  publishedOn: number;
  imageUrl: string;
  title: string;
  subtitle: string;
  authors: string;
  sourceId: string;
  rawBody: string;
  keywords: string;
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  sourceName: string;
  categories: string;
  htmlBody: string;
}

export interface NewsResponse {
  data: NewsItem[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ChatRequest {
  message: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
