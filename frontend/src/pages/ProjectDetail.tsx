import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '@/lib/api';
import { Play, Clock, CheckCircle, XCircle, Loader, AlertCircle } from 'lucide-react';
import type { Project, CrawlJob, Page } from '@/types';

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [crawls, setCrawls] = useState<CrawlJob[]>([]);
  const [pages, setPages] = useState<Page[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCrawlModal, setShowCrawlModal] = useState(false);

  useEffect(() => {
    if (id) {
      loadProjectData(parseInt(id));
    }
  }, [id]);

  const loadProjectData = async (projectId: number) => {
    try {
      setError(null);
      const [projectData, crawlsData, pagesData] = await Promise.all([
        api.getProject(projectId),
        api.getProjectCrawls(projectId).catch(() => []),
        api.getPages(projectId, { limit: 20 }).catch(() => []),
      ]);
      setProject(projectData);
      setCrawls(Array.isArray(crawlsData) ? crawlsData : []);
      setPages(Array.isArray(pagesData) ? pagesData : []);
    } catch (error: any) {
      console.error('Failed to load project data:', error);
      setError(error.response?.data?.detail || 'Failed to load project data');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mb-4"></div>
        <p className="text-gray-600 font-medium">Loading project...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to load project</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button onClick={() => id && loadProjectData(parseInt(id))} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <AlertCircle className="w-16 h-16 text-gray-400 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Project not found</h2>
        <p className="text-gray-600">This project does not exist or you don't have access to it.</p>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'running':
        return <Loader className="w-5 h-5 text-blue-600 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-600 mt-1">{project.domain}</p>
        </div>
        <button
          onClick={() => setShowCrawlModal(true)}
          className="btn btn-primary flex items-center"
        >
          <Play className="w-5 h-5 mr-2" />
          Start Crawl
        </button>
      </div>

      {/* Project Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <p className="text-sm text-gray-600">Total Crawls</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{crawls.length}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Total Pages</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{pages.length}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Avg Response Time</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">-</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Last Crawl</p>
          <p className="text-sm font-medium text-gray-900 mt-1">
            {project.last_crawl_at
              ? new Date(project.last_crawl_at).toLocaleString()
              : 'Never'}
          </p>
        </div>
      </div>

      {/* Recent Crawls */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Crawls</h2>
        {crawls.length === 0 ? (
          <p className="text-gray-600 text-center py-8">
            No crawls yet. Start your first crawl to analyze your website.
          </p>
        ) : (
          <div className="space-y-3">
            {crawls.map((crawl) => (
              <Link
                key={crawl.id}
                to={`/crawls/${crawl.id}`}
                className="block p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(crawl.status)}
                    <div>
                      <p className="font-medium text-gray-900">
                        Crawl #{crawl.id} ({crawl.mode})
                      </p>
                      <p className="text-sm text-gray-500">
                        {new Date(crawl.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <p className="text-gray-900 font-medium">
                      {crawl.pages_crawled} pages
                    </p>
                    <p className="text-gray-500">
                      {crawl.duration_seconds > 0 ? `${crawl.duration_seconds}s` : '-'}
                    </p>
                  </div>
                </div>
                {crawl.error_message && (
                  <p className="mt-2 text-sm text-red-600">{crawl.error_message}</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Recent Pages */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Pages</h2>
        {pages.length === 0 ? (
          <p className="text-gray-600 text-center py-8">
            No pages found. Run a crawl to discover pages.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    URL
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Title
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Words
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {pages.map((page) => (
                  <tr key={page.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                      {page.url}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                      {page.title || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          page.status_code === 200
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {page.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {page.word_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Start Crawl Modal */}
      {showCrawlModal && (
        <StartCrawlModal
          projectId={project.id}
          onClose={() => setShowCrawlModal(false)}
          onSuccess={() => {
            setShowCrawlModal(false);
            loadProjectData(project.id);
          }}
        />
      )}
    </div>
  );
}

function StartCrawlModal({ projectId, onClose, onSuccess }: {
  projectId: number;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [mode, setMode] = useState<'fast' | 'js'>('fast');
  const [config, setConfig] = useState({
    depth: 3,
    max_pages: 100,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await api.startCrawl({ project_id: projectId, mode, config });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start crawl');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Start Crawl</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Crawl Mode</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as 'fast' | 'js')}
              className="input"
            >
              <option value="fast">Fast (Static HTML)</option>
              <option value="js">JavaScript (Playwright)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Max Depth</label>
              <input
                type="number"
                value={config.depth}
                onChange={(e) => setConfig({ ...config, depth: parseInt(e.target.value) })}
                min="1"
                max="10"
                className="input"
              />
            </div>
            <div>
              <label className="label">Max Pages</label>
              <input
                type="number"
                value={config.max_pages}
                onChange={(e) => setConfig({ ...config, max_pages: parseInt(e.target.value) })}
                min="1"
                className="input"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary flex-1"
            >
              {isSubmitting ? 'Starting...' : 'Start Crawl'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
