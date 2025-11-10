import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Link } from 'react-router-dom';
import {
  FolderKanban, Activity, FileText, TrendingUp, ArrowRight,
  AlertCircle, Plus, PlayCircle, CheckCircle, Clock, XCircle
} from 'lucide-react';
import type { Quota, Project, CrawlJob } from '@/types';

export default function Dashboard() {
  const [quota, setQuota] = useState<Quota | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [recentCrawls, setRecentCrawls] = useState<CrawlJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setError(null);
      const [quotaData, projectsData] = await Promise.all([
        api.getQuota().catch(() => null),
        api.getProjects().catch(() => []),
      ]);

      setQuota(quotaData);
      // Ensure projects is always an array
      const projectsList = Array.isArray(projectsData) ? projectsData : [];
      setProjects(projectsList);

      // Load recent crawls for first project
      if (projectsList.length > 0) {
        try {
          const crawls = await api.getProjectCrawls(projectsList[0].id);
          setRecentCrawls(Array.isArray(crawls) ? crawls.slice(0, 5) : []);
        } catch (err) {
          setRecentCrawls([]);
        }
      }
    } catch (error: any) {
      console.error('Failed to load dashboard data:', error);
      setError(error.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mb-4"></div>
        <p className="text-gray-600 font-medium">Loading your dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to load dashboard</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button onClick={loadData} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }

  const currentUsage = quota?.current_usage || {
    total_api_calls: 0,
    pages_crawled: 0,
    crawl_jobs: 0,
    content_generations: 0,
    analysis_requests: 0,
  };

  const stats = [
    {
      name: 'Projects',
      value: projects.length,
      max: quota?.max_projects || 5,
      icon: FolderKanban,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      description: 'Active projects'
    },
    {
      name: 'API Calls',
      value: currentUsage.total_api_calls,
      max: quota?.max_api_calls_per_month || 10000,
      icon: Activity,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      description: 'This month'
    },
    {
      name: 'Pages Crawled',
      value: currentUsage.pages_crawled,
      max: quota?.max_pages_per_crawl || 1000,
      icon: FileText,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      description: 'Total pages'
    },
    {
      name: 'Crawl Jobs',
      value: currentUsage.crawl_jobs,
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      description: 'This month'
    },
  ];

  const getCrawlStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'running':
        return <PlayCircle className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getUsagePercentage = (current: number, max: number) => {
    return Math.min((current / max) * 100, 100);
  };

  const usagePercent = getUsagePercentage(
    currentUsage.total_api_calls,
    quota?.max_api_calls_per_month || 10000
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Welcome back! Here's an overview of your SEO projects.
          </p>
        </div>
        <Link to="/projects" className="btn btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Link>
      </div>

      {/* Quota Warning */}
      {quota && usagePercent > 80 && (
        <div className={`p-4 border rounded-lg ${
          usagePercent > 95
            ? 'bg-red-50 border-red-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-start">
            <AlertCircle className={`w-5 h-5 mt-0.5 mr-3 ${
              usagePercent > 95 ? 'text-red-600' : 'text-yellow-600'
            }`} />
            <div>
              <p className={`font-medium ${
                usagePercent > 95 ? 'text-red-900' : 'text-yellow-900'
              }`}>
                {usagePercent > 95 ? 'Quota Limit Reached' : 'Approaching Quota Limit'}
              </p>
              <p className={`text-sm mt-1 ${
                usagePercent > 95 ? 'text-red-700' : 'text-yellow-700'
              }`}>
                You've used {Math.round(usagePercent)}% of your monthly API quota.
                {usagePercent > 95
                  ? ' Consider upgrading your plan to continue.'
                  : ' Consider upgrading your plan soon.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const percentage = stat.max ? getUsagePercentage(stat.value, stat.max) : 0;
          return (
            <div key={stat.name} className="card hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <div className="mt-2">
                    <span className="text-3xl font-bold text-gray-900">{stat.value.toLocaleString()}</span>
                    {stat.max && (
                      <span className="text-gray-500 text-sm ml-2">/ {stat.max.toLocaleString()}</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{stat.description}</p>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
              {stat.max && (
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        percentage > 80 ? 'bg-red-500' : percentage > 50 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Projects */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">Projects</h2>
            <Link to="/projects" className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center">
              View all <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>

          {projects.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
              <FolderKanban className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
              <p className="text-gray-600 mb-6 max-w-sm mx-auto">
                Create your first project to start crawling and analyzing your website.
              </p>
              <Link to="/projects" className="btn btn-primary inline-flex items-center">
                <Plus className="w-4 h-4 mr-2" />
                Create Project
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {projects.slice(0, 5).map((project) => (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="block p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <FolderKanban className="w-5 h-5 text-gray-400 mr-2" />
                        <h3 className="font-medium text-gray-900">{project.name}</h3>
                      </div>
                      <p className="text-sm text-gray-500 mt-1 ml-7">{project.domain}</p>
                      <div className="flex items-center gap-4 mt-2 ml-7 text-xs text-gray-500">
                        <span>Max depth: {project.max_depth}</span>
                        <span>•</span>
                        <span>Max pages: {project.max_pages}</span>
                      </div>
                    </div>
                    {project.last_crawl_at && (
                      <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                        {new Date(project.last_crawl_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent Crawls */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">Recent Crawls</h2>
          </div>

          {recentCrawls.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
              <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No crawls yet</h3>
              <p className="text-gray-600 mb-6 max-w-sm mx-auto">
                Start a crawl job to analyze your website structure and content.
              </p>
              {projects.length > 0 && (
                <Link to={`/projects/${projects[0].id}`} className="btn btn-primary inline-flex items-center">
                  <PlayCircle className="w-4 h-4 mr-2" />
                  Start Crawl
                </Link>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {recentCrawls.map((crawl) => (
                <div
                  key={crawl.id}
                  className="p-4 border border-gray-200 rounded-lg"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      {getCrawlStatusIcon(crawl.status)}
                      <span className="ml-2 font-medium text-gray-900 capitalize">
                        {crawl.status}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(crawl.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>Mode: {crawl.mode}</span>
                    <span>•</span>
                    <span>{crawl.pages_crawled} pages</span>
                    {crawl.completed_at && (
                      <>
                        <span>•</span>
                        <span>
                          Duration: {Math.round((new Date(crawl.completed_at).getTime() - new Date(crawl.created_at).getTime()) / 1000)}s
                        </span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/projects"
            className="p-6 border-2 border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-all text-center"
          >
            <FolderKanban className="w-10 h-10 text-primary-600 mx-auto mb-3" />
            <h3 className="font-medium text-gray-900 mb-1">Manage Projects</h3>
            <p className="text-sm text-gray-600">Create and configure your SEO projects</p>
          </Link>

          <Link
            to="/usage"
            className="p-6 border-2 border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-all text-center"
          >
            <Activity className="w-10 h-10 text-primary-600 mx-auto mb-3" />
            <h3 className="font-medium text-gray-900 mb-1">View Usage</h3>
            <p className="text-sm text-gray-600">Monitor your quota and usage stats</p>
          </Link>

          <div className="p-6 border-2 border-gray-200 rounded-lg text-center opacity-50 cursor-not-allowed">
            <TrendingUp className="w-10 h-10 text-gray-400 mx-auto mb-3" />
            <h3 className="font-medium text-gray-900 mb-1">Analytics</h3>
            <p className="text-sm text-gray-600">Coming soon</p>
          </div>
        </div>
      </div>
    </div>
  );
}
