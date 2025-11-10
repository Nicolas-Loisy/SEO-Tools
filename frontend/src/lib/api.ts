const API_URL = ((import.meta as any).env?.VITE_API_URL as string) || '';

function getApiKey(): string | null {
  return localStorage.getItem('api_key');
}

function setApiKey(key: string) {
  localStorage.setItem('api_key', key);
}

function clearApiKey() {
  localStorage.removeItem('api_key');
}

function authHeaders(): Record<string, string> {
  const key = getApiKey();
  return key ? { 'x-api-key': key } : {};
}

async function request(path: string, opts: RequestInit = {}) {
  const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
  const url = `${base}${path.startsWith('/') ? path : '/' + path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...authHeaders(),
    ...(opts.headers as Record<string, string> || {}),
  };

  const res = await fetch(url, { ...opts, headers });

  const text = await res.text();
  const contentType = res.headers.get('content-type') || '';
  let data: any = null;
  if (text && contentType.includes('application/json')) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  } else if (text) {
    data = text;
  }

  if (!res.ok) {
    const error: any = new Error(data?.detail || res.statusText || 'Request failed');
    error.response = { data, status: res.status };
    throw error;
  }

  if (res.status === 204) return null;
  return data;
}

export const api = {
  getApiKey,
  setApiKey,
  clearApiKey,

  // Quota / usage
  getQuota: async () => {
    return request('/usage/quota', { method: 'GET' });
  },
  getUsageHistory: async (months = 6) => {
    return request(`/usage?months=${months}`, { method: 'GET' });
  },

  // Projects
  getProjects: async () => {
    return request('/projects', { method: 'GET' });
  },
  getProject: async (id: number) => {
    return request(`/projects/${id}`, { method: 'GET' });
  },
  createProject: async (data: any) => {
    return request('/projects', { method: 'POST', body: JSON.stringify(data) });
  },
  deleteProject: async (id: number) => {
    return request(`/projects/${id}`, { method: 'DELETE' });
  },

  // Crawls / pages
  getProjectCrawls: async (projectId: number) => {
    return request(`/projects/${projectId}/crawls`, { method: 'GET' });
  },
  getPages: async (projectId: number, params: { limit?: number } = {}) => {
    const limit = params.limit ?? 20;
    return request(`/projects/${projectId}/pages?limit=${limit}`, { method: 'GET' });
  },
  startCrawl: async ({ project_id, mode, config }: { project_id: number; mode: string; config?: any }) => {
    if (project_id) {
      return request(`/projects/${project_id}/crawls`, {
        method: 'POST',
        body: JSON.stringify({ mode, config }),
      });
    }
    return request('/crawls', { method: 'POST', body: JSON.stringify({ project_id, mode, config }) });
  },
};
