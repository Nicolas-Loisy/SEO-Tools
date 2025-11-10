import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Link } from 'react-router-dom';
import { FolderKanban, Activity, FileText, TrendingUp, ArrowRight } from 'lucide-react';
import type { Quota, Project, CrawlJob } from '@/types';

export default function Dashboard() {
  const [quota, setQuota] = useState<Quota | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [recentCrawls, setRecentCrawls] = useState<CrawlJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [quotaData, projectsData] = await Promise.all([
        api.getQuota(),
        api.getProjects(),
      ]);
      setQuota(quotaData);
      setProjects(projectsData);

      // Load recent crawls for first project
      if (projectsData.length > 0) {
        const crawls = await api.getProjectCrawls(projectsData[0].id);
        setRecentCrawls(crawls.slice(0, 5));
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const stats = [
    {
      name: 'Projects',
      value: projects.length,
      max: quota?.max_projects || 0,
      icon: FolderKanban,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      name: 'API Calls',
      value: quota?.current_usage.total_api_calls || 0,
      max: quota?.max_api_calls_per_month || 0,
      icon: Activity,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      name: 'Pages Crawled',
      value: quota?.current_usage.pages_crawled || 0,
      icon: FileText,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      name: 'Crawl Jobs',
      value: quota?.current_usage.crawl_jobs || 0,
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Welcome back! Here's what's happening with your projects.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <div className="mt-1">
                  <span className="text-3xl font-bold text-gray-900">{stat.value}</span>
                  {stat.max && (
                    <span className="text-gray-500 text-sm ml-2">/ {stat.max}</span>
                  )}
                </div>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quota Warning */}
      {quota && quota.remaining.api_calls < quota.max_api_calls_per_month * 0.2 && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-800">
            <strong>Warning:</strong> You're approaching your API quota limit. Consider upgrading your plan.
          </p>
        </div>
      )}

      {/* Recent Projects */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Projects</h2>
          <Link to="/projects" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
            View all <ArrowRight className="inline w-4 h-4" />
          </Link>
        </div>
        {projects.length === 0 ? (
          <div className="text-center py-8">
            <FolderKanban className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 mb-4">No projects yet</p>
            <Link to="/projects" className="btn btn-primary">
              Create your first project
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {projects.slice(0, 5).map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="block p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">{project.name}</h3>
                    <p className="text-sm text-gray-500">{project.domain}</p>
                  </div>
                  {project.last_crawl_at && (
                    <span className="text-xs text-gray-500">
                      Last crawl: {new Date(project.last_crawl_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
