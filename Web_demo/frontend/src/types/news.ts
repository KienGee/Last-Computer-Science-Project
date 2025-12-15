// src/types/news.ts

export interface CrawledNews {
  title: string;
  body: string;
  source: string;
  url?: string | null;
  published_at?: string | null;

  summary: string;
  category: string;  // Category từ URL
}

export interface PreviewRequest {
  title?: string;
  body: string;
}

export interface PreviewResponse {
  summary: string;

  category: string;
  score: number;

  secondary_category?: string | null;
  secondary_score?: number | null;
}
