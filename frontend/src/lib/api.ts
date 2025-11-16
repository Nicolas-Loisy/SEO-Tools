import axios, { AxiosInstance } from 'axios';
import type { Project, CrawlJob, Page, Quota, UsageStats } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class APIClient {
  private client: AxiosInstance;
  private apiKey: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      // Follow redirects automatically
      maxRedirects: 5,
    });

    // Load API key from localStorage
    this.apiKey = localStorage.getItem('apiKey');
    if (this.apiKey) {
      this.setApiKey(this.apiKey);
    }

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Clear invalid API key
          this.clearApiKey();
          window.location.href = '/';
        }
        return Promise.reject(error);
      }
    );
  }

  setApiKey(key: string) {
    this.apiKey = key;
    localStorage.setItem('apiKey', key);
    this.client.defaults.headers.common['X-API-Key'] = key;
  }

  clearApiKey() {
    this.apiKey = null;
    localStorage.removeItem('apiKey');
    delete this.client.defaults.headers.common['X-API-Key'];
  }

  getApiKey(): string | null {
    return this.apiKey;
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    const { data } = await this.client.get('/projects/');
    return data;
  }

  async getProject(id: number): Promise<Project> {
    const { data } = await this.client.get(`/projects/${id}`);
    return data;
  }

  async createProject(project: Partial<Project>): Promise<Project> {
    const { data } = await this.client.post('/projects/', project);
    return data;
  }

  async updateProject(id: number, project: Partial<Project>): Promise<Project> {
    const { data } = await this.client.put(`/projects/${id}`, project);
    return data;
  }

  async deleteProject(id: number): Promise<void> {
    await this.client.delete(`/projects/${id}`);
  }

  // Crawl Jobs
  async startCrawl(payload: {
    project_id: number;
    mode: 'fast' | 'js';
    config?: Record<string, any>;
  }): Promise<CrawlJob> {
    const { data } = await this.client.post('/crawl/', payload);
    return data;
  }

  async getCrawlJob(id: number): Promise<CrawlJob> {
    const { data } = await this.client.get(`/crawl/${id}`);
    return data;
  }

  async getProjectCrawls(projectId: number): Promise<CrawlJob[]> {
    const { data } = await this.client.get(`/crawl/project/${projectId}`);
    return data;
  }

  async getCrawlPages(crawlJobId: number, skip: number = 0, limit: number = 100): Promise<{
    items: Page[];
    total: number;
    skip: number;
    limit: number;
    has_next: boolean;
  }> {
    const { data } = await this.client.get(`/crawl/${crawlJobId}/pages`, {
      params: { skip, limit },
    });
    return data;
  }

  // Pages
  async getPages(projectId: number, params?: {
    skip?: number;
    limit?: number;
  }): Promise<Page[]> {
    const { data } = await this.client.get('/pages/', {
      params: { project_id: projectId, ...params },
    });
    return data;
  }

  async getPage(id: number): Promise<Page> {
    const { data } = await this.client.get(`/pages/${id}`);
    return data;
  }

  // Usage & Quotas
  async getQuota(): Promise<Quota> {
    const { data } = await this.client.get('/usage/quota');
    return data;
  }

  async getUsageStats(year?: number, month?: number): Promise<UsageStats> {
    const { data } = await this.client.get('/usage/stats', {
      params: { year, month },
    });
    return data;
  }

  async getUsageHistory(months: number = 6): Promise<{ history: UsageStats[] }> {
    const { data } = await this.client.get('/usage/history', {
      params: { months },
    });
    return data;
  }

  // Content Generation
  async generateMetaDescription(payload: {
    page_id: number;
    max_length?: number;
    provider?: string;
  }): Promise<{ generated_description: string }> {
    const { data } = await this.client.post('/content/meta-description', payload);
    return data;
  }

  async generateTitleSuggestions(payload: {
    page_id: number;
    count?: number;
    provider?: string;
  }): Promise<{ suggestions: string[] }> {
    const { data } = await this.client.post('/content/title-suggestions', payload);
    return data;
  }

  async generateRecommendations(payload: {
    page_id: number;
    provider?: string;
  }): Promise<{ recommendations: Record<string, any> }> {
    const { data } = await this.client.post('/content/recommendations', payload);
    return data;
  }

  // Analysis
  async generateEmbeddings(projectId: number): Promise<any> {
    const { data } = await this.client.post(`/analysis/projects/${projectId}/embeddings`);
    return data;
  }

  async computeGraph(projectId: number): Promise<any> {
    const { data } = await this.client.post(`/analysis/projects/${projectId}/graph`);
    return data;
  }

  async getRecommendations(projectId: number, topK: number = 5): Promise<any> {
    const { data } = await this.client.post(`/analysis/projects/${projectId}/recommendations`, null, {
      params: { top_k: topK },
    });
    return data;
  }

  // Search
  async searchPages(params: {
    q: string;
    project_id?: number;
    status_code?: number;
    min_seo_score?: number;
    max_seo_score?: number;
    min_word_count?: number;
    limit?: number;
    offset?: number;
  }): Promise<{
    query: string;
    hits: any[];
    total: number;
    limit: number;
    offset: number;
    processing_time_ms: number;
  }> {
    const { data } = await this.client.get('/search/', { params });
    return data;
  }

  async reindexPages(): Promise<{
    success: boolean;
    message: string;
    indexed_count: number;
  }> {
    const { data } = await this.client.post('/search/reindex');
    return data;
  }

  async getSearchStats(): Promise<{
    status: string;
    index_name: string;
    number_of_documents: number;
    is_indexing: boolean;
    field_distribution?: Record<string, number>;
    error?: string;
  }> {
    const { data } = await this.client.get('/search/stats');
    return data;
  }

  // Internal Linking Analysis
  async getLinkRecommendations(
    projectId: number,
    pageId?: number,
    limit: number = 20
  ): Promise<{
    project_id: number;
    page_id?: number;
    recommendations: Array<{
      source_page_id?: number;
      source_url?: string;
      target_page_id: number;
      target_url: string;
      target_title: string;
      keyword: string;
      context: string;
      score: number;
      reason: string;
    }>;
    count: number;
  }> {
    const params: any = { limit };
    if (pageId) params.page_id = pageId;
    const { data } = await this.client.get(`/analysis/projects/${projectId}/link-recommendations`, { params });
    return data;
  }

  async getLinkGraphAnalysis(projectId: number): Promise<{
    project_id: number;
    total_pages: number;
    total_links: number;
    avg_links_per_page: number;
    orphan_pages: number;
    hub_pages: Array<{
      page_id: number;
      url: string;
      title: string;
      seo_score: number;
      pagerank: number;
      in_degree: number;
      out_degree: number;
    }>;
    authority_pages: Array<{
      page_id: number;
      url: string;
      title: string;
      seo_score: number;
      pagerank: number;
      in_degree: number;
      out_degree: number;
    }>;
  }> {
    const { data } = await this.client.get(`/analysis/projects/${projectId}/link-graph`);
    return data;
  }

  async exportLinkGraph(projectId: number): Promise<{
    project_id: number;
    graph: {
      nodes: Array<{
        id: number;
        label: string;
        url: string;
        seo_score: number;
        depth: number;
        pagerank: number;
        in_degree: number;
        out_degree: number;
      }>;
      edges: Array<{
        source: number;
        target: number;
      }>;
    };
  }> {
    const { data } = await this.client.get(`/analysis/projects/${projectId}/link-graph/export`);
    return data;
  }

  async getAnchorTextAnalysis(projectId: number, maxPages: number = 1000): Promise<{
    project_id: number;
    stats: {
      total_links: number;
      links_with_anchor_text: number;
      links_without_anchor_text: number;
      generic_anchors_count: number;
      generic_anchors_percentage: number;
      top_anchor_texts: Array<{
        anchor_text: string;
        count: number;
        percentage: number;
      }>;
      generic_anchors: Array<{
        anchor_text: string;
        count: number;
        percentage: number;
      }>;
      over_optimized_anchors: Array<{
        anchor_text: string;
        count: number;
        percentage: number;
        severity: string;
      }>;
      average_anchor_length: number;
      unique_anchor_texts: number;
    };
    recommendations: Array<{
      type: string;
      severity: string;
      title: string;
      message: string;
      count?: number;
      examples?: string[];
      average_length?: number;
    }>;
  }> {
    const { data } = await this.client.get(`/analysis/projects/${projectId}/anchor-text-analysis`, {
      params: { max_pages: maxPages }
    });
    return data;
  }

  // Structured Data / Schema.org
  async detectSchemaTypes(projectId: number, pageId: number): Promise<{
    page_id: number;
    url: string;
    detected_types: Array<{
      type: string;
      priority: number;
    }>;
  }> {
    const { data } = await this.client.get(`/analysis/projects/${projectId}/pages/${pageId}/schema/detect`);
    return data;
  }

  async generateJSONLD(
    projectId: number,
    pageId: number,
    schemaType: string,
    additionalData?: Record<string, any>
  ): Promise<{
    page_id: number;
    schema_type: string;
    schema: Record<string, any>;
    html: string;
    validation: {
      valid: boolean;
      errors: string[];
      warnings: string[];
    };
  }> {
    const { data } = await this.client.post(
      `/analysis/projects/${projectId}/pages/${pageId}/schema/generate`,
      { additional_data: additionalData },
      { params: { schema_type: schemaType } }
    );
    return data;
  }

  async validateJSONLD(
    projectId: number,
    pageId: number,
    schema: Record<string, any>
  ): Promise<{
    page_id: number;
    validation: {
      valid: boolean;
      errors: string[];
      warnings: string[];
    };
  }> {
    const { data } = await this.client.post(
      `/analysis/projects/${projectId}/pages/${pageId}/schema/validate`,
      { schema }
    );
    return data;
  }

  async bulkDetectSchemas(projectId: number, limit: number = 50): Promise<{
    project_id: number;
    total_pages: number;
    pages: Array<{
      page_id: number;
      url: string;
      title: string;
      detected_types: string[];
    }>;
  }> {
    const { data } = await this.client.get(`/analysis/projects/${projectId}/schema/bulk-detect`, {
      params: { limit }
    });
    return data;
  }

  async enhanceSchemaWithAI(
    projectId: number,
    pageId: number,
    schema: Record<string, any>,
    provider: string = 'openai'
  ): Promise<{
    page_id: number;
    enhanced_schema: Record<string, any>;
    improvements: string[];
    recommendations: string[];
    provider: string;
  }> {
    const { data } = await this.client.post(
      `/analysis/projects/${projectId}/pages/${pageId}/schema/enhance`,
      { schema },
      { params: { provider } }
    );
    return data;
  }
}

export const api = new APIClient();
