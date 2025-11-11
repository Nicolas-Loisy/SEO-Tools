import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '@/lib/api';
import {
  ArrowLeft, Clock, CheckCircle, XCircle, PlayCircle, FileText,
  ExternalLink, AlertCircle, Download, RefreshCw
} from 'lucide-react';
import type { CrawlJob, Page } from '@/types';

export default function CrawlDetails() {
  const { crawlId } = useParams<{ crawlId: string }>();
  const [crawl, setCrawl] = useState<CrawlJob | null>(null);
  const [pages, setPages] = useState<Page[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(50);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (crawlId) {
      loadData();
    }
  }, [crawlId, skip]);

  useEffect(() => {
    // Auto-refresh if crawl is in progress
    if (crawl && (crawl.status === 'pending' || crawl.status === 'running')) {
      const interval = setInterval(() => {
        loadData();
      }, 5000); // Refresh every 5 seconds

      return () => clearInterval(interval);
    }
  }, [crawl]);

  const loadData = async () => {
    try {
      setError(null);
      const [crawlData, pagesData] = await Promise.all([
        api.getCrawlJob(Number(crawlId)),
        api.getCrawlPages(Number(crawlId), skip, limit),
      ]);

      setCrawl(crawlData);
      setPages(pagesData.items);
      setTotal(pagesData.total);
    } catch (error: any) {
      console.error('Failed to load crawl details:', error);
      setError(error.response?.data?.detail || 'Failed to load crawl details');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'running':
        return <PlayCircle className="w-6 h-6 text-blue-500 animate-pulse" />;
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Clock className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusCodeColor = (code?: number) => {
    if (!code) return 'text-gray-500';
    if (code >= 200 && code < 300) return 'text-green-600';
    if (code >= 300 && code < 400) return 'text-yellow-600';
    if (code >= 400 && code < 500) return 'text-orange-600';
    if (code >= 500) return 'text-red-600';
    return 'text-gray-500';
  };

  const getSEOScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 70) return 'text-blue-600 bg-blue-50';
    if (score >= 50) return 'text-yellow-600 bg-yellow-50';
    if (score >= 30) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const exportToCSV = () => {
    if (pages.length === 0) return;

    const headers = ['URL', 'Status Code', 'Title', 'H1', 'Meta Description', 'Word Count', 'Internal Links', 'External Links', 'Depth'];
    const rows = pages.map(page => [
      page.url,
      page.status_code || '',
      page.title || '',
      page.h1 || '',
      page.meta_description || '',
      page.word_count,
      page.internal_links_count,
      page.external_links_count,
      page.depth,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `crawl-${crawlId}-pages.csv`;
    link.click();
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mb-4"></div>
        <p className="text-gray-600 font-medium">Loading crawl details...</p>
      </div>
    );
  }

  if (error || !crawl) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
        <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to load crawl</h2>
        <p className="text-gray-600 mb-4">{error || 'Crawl not found'}</p>
        <Link to={`/projects/${crawl?.project_id || ''}`} className="btn btn-primary">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Project
        </Link>
      </div>
    );
  }

  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            to={`/projects/${crawl.project_id}`}
            className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Project
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Crawl Details</h1>
          <p className="text-gray-600 mt-1">
            Crawl #{crawl.id} • {new Date(crawl.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {(crawl.status === 'pending' || crawl.status === 'running') && (
            <button onClick={loadData} className="btn btn-secondary">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
          )}
          <button
            onClick={exportToCSV}
            disabled={pages.length === 0}
            className="btn btn-primary"
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Status Card */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Status</p>
            <div className="flex items-center gap-2">
              {getStatusIcon(crawl.status)}
              <span className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${getStatusColor(crawl.status)}`}>
                {crawl.status}
              </span>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Mode</p>
            <p className="text-2xl font-bold text-gray-900 capitalize">{crawl.mode}</p>
            <p className="text-xs text-gray-500">{crawl.mode === 'js' ? 'JavaScript Rendering' : 'Fast HTTP'}</p>
          </div>

          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Pages Crawled</p>
            <p className="text-2xl font-bold text-gray-900">{crawl.pages_crawled.toLocaleString()}</p>
            {crawl.pages_failed > 0 && (
              <p className="text-xs text-red-600">{crawl.pages_failed} failed</p>
            )}
          </div>

          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Duration</p>
            <p className="text-2xl font-bold text-gray-900">
              {crawl.status === 'running' && crawl.started_at
                ? `${Math.round((new Date().getTime() - new Date(crawl.started_at).getTime()) / 1000)}s`
                : `${Math.round(crawl.duration_seconds)}s`}
            </p>
            {crawl.started_at && (
              <p className="text-xs text-gray-500">
                Started {new Date(crawl.started_at).toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>

        {crawl.error_message && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3" />
              <div>
                <p className="font-medium text-red-900">Error</p>
                <p className="text-sm text-red-700 mt-1">{crawl.error_message}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Pages Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Crawled Pages</h2>
            <p className="text-sm text-gray-600 mt-1">
              Showing {skip + 1}-{Math.min(skip + limit, total)} of {total} pages
            </p>
          </div>
        </div>

        {pages.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No pages crawled yet</h3>
            <p className="text-gray-600">
              {crawl.status === 'running' ? 'Crawling in progress...' : 'This crawl has not discovered any pages.'}
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      URL
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Title
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Words
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Links
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      SEO Score
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Depth
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {pages.map((page) => (
                    <tr key={page.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <a
                            href={page.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:text-primary-700 text-sm font-medium truncate max-w-md"
                            title={page.url}
                          >
                            {page.url}
                          </a>
                          <ExternalLink className="w-3 h-3 text-gray-400 flex-shrink-0" />
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-sm font-medium ${getStatusCodeColor(page.status_code)}`}>
                          {page.status_code || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-sm text-gray-900 truncate max-w-xs" title={page.title || ''}>
                          {page.title || '-'}
                        </p>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {page.word_count.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {page.internal_links_count} / {page.external_links_count}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-sm font-medium ${getSEOScoreColor(page.seo_score)}`}>
                          {Math.round(page.seo_score)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {page.depth}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 sm:px-6">
                <div className="flex justify-between sm:hidden">
                  <button
                    onClick={() => setSkip(Math.max(0, skip - limit))}
                    disabled={skip === 0}
                    className="btn btn-secondary"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setSkip(skip + limit)}
                    disabled={skip + limit >= total}
                    className="btn btn-secondary ml-3"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Page <span className="font-medium">{currentPage}</span> of{' '}
                      <span className="font-medium">{totalPages}</span>
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSkip(Math.max(0, skip - limit))}
                      disabled={skip === 0}
                      className="btn btn-secondary"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setSkip(skip + limit)}
                      disabled={skip + limit >= total}
                      className="btn btn-secondary"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
