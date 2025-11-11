export interface Project {
  id: number;
  name: string;
  domain: string;
  max_depth: number;
  max_pages: number;
  crawl_delay: number;
  respect_robots: boolean;
  last_crawl_at?: string;
  created_at: string;
}

export interface CrawlJob {
  id: number;
  project_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  mode: 'fast' | 'js';
  config: Record<string, any>;
  started_at?: string;
  finished_at?: string;
  duration_seconds: number;
  pages_discovered: number;
  pages_crawled: number;
  pages_failed: number;
  links_found: number;
  error_message?: string;
  created_at: string;
}

export interface Page {
  id: number;
  project_id: number;
  crawl_job_id: number;
  url: string;
  status_code?: number;
  content_type?: string;
  title?: string;
  meta_description?: string;
  meta_keywords?: string;
  h1?: string;
  word_count: number;
  lang?: string;
  depth: number;
  seo_score: number;
  internal_links_count: number;
  external_links_count: number;
  discovered_at: string;
  last_crawled_at?: string;
}

export interface UsageStats {
  period: string;
  total_api_calls: number;
  crawl_jobs: number;
  pages_crawled: number;
  analysis_requests: number;
}

export interface Quota {
  plan: string;
  max_projects: number;
  max_pages_per_crawl: number;
  max_api_calls_per_month: number;
  current_usage: UsageStats;
  remaining: {
    api_calls: number;
    projects: number;
    pages_per_crawl: number;
  };
}

export interface ContentGeneration {
  page_id: number;
  generated_description?: string;
  suggestions?: string[];
  recommendations?: Record<string, any>;
}
