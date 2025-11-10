import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Link } from 'react-router-dom';
import { Plus, FolderKanban, Trash2, ExternalLink, Search, X, AlertCircle } from 'lucide-react';
import type { Project } from '@/types';

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setError(null);
      const data = await api.getProjects();
      setProjects(data);
    } catch (error: any) {
      console.error('Failed to load projects:', error);
      setError(error.response?.data?.detail || 'Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This will permanently delete all associated data.`)) return;

    try {
      await api.deleteProject(id);
      setProjects(projects.filter(p => p.id !== id));
    } catch (error: any) {
      console.error('Failed to delete project:', error);
      alert(error.response?.data?.detail || 'Failed to delete project');
    }
  };

  const filteredProjects = projects.filter((project) =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.domain.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mb-4"></div>
        <p className="text-gray-600 font-medium">Loading projects...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600 mt-1">
            Manage your SEO projects and crawling configurations
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center"
        >
          <Plus className="w-5 h-5 mr-2" />
          New Project
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3" />
          <div className="flex-1">
            <p className="font-medium text-red-900">Error</p>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-red-600 hover:text-red-700">
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Search Bar */}
      {projects.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search projects by name or domain..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-10 w-full max-w-md"
          />
        </div>
      )}

      {filteredProjects.length === 0 ? (
        <div className="card text-center py-16 border-2 border-dashed">
          <FolderKanban className="w-20 h-20 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            {searchQuery ? 'No projects found' : 'No projects yet'}
          </h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            {searchQuery
              ? 'Try adjusting your search query'
              : 'Get started by creating your first project to crawl and analyze your website'}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary inline-flex items-center"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Project
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <div key={project.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
                    {project.name}
                  </h3>
                  <a
                    href={project.domain}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center truncate"
                  >
                    {project.domain}
                    <ExternalLink className="w-3 h-3 ml-1 flex-shrink-0" />
                  </a>
                </div>
                <button
                  onClick={() => handleDelete(project.id, project.name)}
                  className="text-gray-400 hover:text-red-600 transition-colors flex-shrink-0 ml-2"
                  title="Delete project"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div className="flex justify-between">
                  <span>Max Depth:</span>
                  <span className="font-medium">{project.max_depth}</span>
                </div>
                <div className="flex justify-between">
                  <span>Max Pages:</span>
                  <span className="font-medium">{project.max_pages.toLocaleString()}</span>
                </div>
                {project.last_crawl_at && (
                  <div className="flex justify-between">
                    <span>Last Crawl:</span>
                    <span className="font-medium">
                      {new Date(project.last_crawl_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>

              <Link
                to={`/projects/${project.id}`}
                className="btn btn-secondary w-full text-center"
              >
                View Details
              </Link>
            </div>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <CreateProjectModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadProjects();
          }}
        />
      )}
    </div>
  );
}

function CreateProjectModal({ onClose, onSuccess }: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    max_depth: 3,
    max_pages: 100,
    crawl_delay: 1.0,
    respect_robots: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await api.createProject(formData);
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Create Project</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Project Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              required
            />
          </div>

          <div>
            <label className="label">Domain</label>
            <input
              type="url"
              value={formData.domain}
              onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
              placeholder="https://example.com"
              className="input"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Max Depth</label>
              <input
                type="number"
                value={formData.max_depth}
                onChange={(e) => setFormData({ ...formData, max_depth: parseInt(e.target.value) })}
                min="1"
                max="10"
                className="input"
              />
            </div>
            <div>
              <label className="label">Max Pages</label>
              <input
                type="number"
                value={formData.max_pages}
                onChange={(e) => setFormData({ ...formData, max_pages: parseInt(e.target.value) })}
                min="1"
                className="input"
              />
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="respect_robots"
              checked={formData.respect_robots}
              onChange={(e) => setFormData({ ...formData, respect_robots: e.target.checked })}
              className="w-4 h-4 text-primary-600 rounded"
            />
            <label htmlFor="respect_robots" className="ml-2 text-sm text-gray-700">
              Respect robots.txt
            </label>
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
              {isSubmitting ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
