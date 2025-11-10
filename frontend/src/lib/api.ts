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
}

export const api = new APIClient();
