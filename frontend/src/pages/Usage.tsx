import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { TrendingUp, Activity, FileText, Zap, AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { Quota, UsageStats } from '@/types';

export default function Usage() {
  const [quota, setQuota] = useState<Quota | null>(null);
  const [history, setHistory] = useState<UsageStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setError(null);
      const [quotaData, historyData] = await Promise.all([
        api.getQuota(),
        api.getUsageHistory(6),
      ]);
      setQuota(quotaData);
      setHistory(historyData?.history || []);
    } catch (error: any) {
      console.error('Failed to load usage data:', error);
      setError(error.response?.data?.detail || 'Failed to load usage data');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mb-4"></div>
        <p className="text-gray-600 font-medium">Loading usage data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to load usage data</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button onClick={loadData} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }

  if (!quota) return null;

  // Safe access to quota data with fallbacks
  const currentUsage = quota.current_usage || {
    total_api_calls: 0,
    crawl_jobs: 0,
    pages_crawled: 0,
    content_generations: 0,
    analysis_requests: 0,
  };

  const remaining = quota.remaining || {
    api_calls: 0,
    projects: 0,
    pages_per_crawl: 0,
  };

  const usagePercent = quota.max_api_calls_per_month > 0
    ? (currentUsage.total_api_calls / quota.max_api_calls_per_month) * 100
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Usage & Quotas</h1>
        <p className="text-gray-600 mt-1">
          Monitor your API usage and manage your subscription
        </p>
      </div>

      {/* Plan Card */}
      <div className="card bg-gradient-to-br from-primary-500 to-primary-700 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-primary-100 mb-1">Current Plan</p>
            <h2 className="text-3xl font-bold capitalize">{quota.plan}</h2>
          </div>
          <Zap className="w-12 h-12 text-primary-200" />
        </div>
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div>
            <p className="text-primary-100 text-sm">Projects</p>
            <p className="text-2xl font-bold">{quota.max_projects}</p>
          </div>
          <div>
            <p className="text-primary-100 text-sm">Pages/Crawl</p>
            <p className="text-2xl font-bold">{quota.max_pages_per_crawl}</p>
          </div>
          <div>
            <p className="text-primary-100 text-sm">API Calls</p>
            <p className="text-2xl font-bold">
              {quota.max_api_calls_per_month.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Usage Progress */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">API Usage This Month</h2>
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-gray-600">
            {currentUsage.total_api_calls.toLocaleString()} of{' '}
            {quota.max_api_calls_per_month.toLocaleString()} calls
          </span>
          <span className="font-medium text-gray-900">{usagePercent.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className={`h-4 rounded-full transition-all ${
              usagePercent > 90
                ? 'bg-red-600'
                : usagePercent > 75
                ? 'bg-yellow-600'
                : 'bg-green-600'
            }`}
            style={{ width: `${Math.min(usagePercent, 100)}%` }}
          />
        </div>
        {usagePercent > 80 && (
          <p className="mt-3 text-sm text-yellow-700 bg-yellow-50 p-3 rounded-lg">
            You're approaching your monthly limit. Consider upgrading your plan.
          </p>
        )}
      </div>

      {/* Current Period Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Crawl Jobs</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {currentUsage.crawl_jobs}
              </p>
            </div>
            <Activity className="w-10 h-10 text-blue-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pages Crawled</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {currentUsage.pages_crawled}
              </p>
            </div>
            <FileText className="w-10 h-10 text-green-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Analysis Requests</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {currentUsage.analysis_requests}
              </p>
            </div>
            <TrendingUp className="w-10 h-10 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Usage History Chart */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Usage Trend</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={history.slice().reverse()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total_api_calls" fill="#3b82f6" name="API Calls" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Remaining Quotas */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Remaining Quotas</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-700">API Calls</span>
            <span className="font-bold text-gray-900">
              {remaining.api_calls.toLocaleString()} remaining
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Projects</span>
            <span className="font-bold text-gray-900">
              {remaining.projects} available
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Pages per Crawl</span>
            <span className="font-bold text-gray-900">
              {remaining.pages_per_crawl} maximum
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
