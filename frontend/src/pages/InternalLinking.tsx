import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '@/lib/api';
import { Link as LinkIcon, TrendingUp, ExternalLink, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

export default function InternalLinking() {
  const { id } = useParams<{ id: string }>();
  const projectId = parseInt(id || '0');

  const [activeTab, setActiveTab] = useState<'recommendations' | 'analysis'>('recommendations');
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [graphAnalysis, setGraphAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (activeTab === 'recommendations') {
      loadRecommendations();
    } else {
      loadGraphAnalysis();
    }
  }, [activeTab, projectId]);

  const loadRecommendations = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getLinkRecommendations(projectId);
      setRecommendations(data.recommendations);
    } catch (err: any) {
      setError(err.message || 'Failed to load recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  const loadGraphAnalysis = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getLinkGraphAnalysis(projectId);
      setGraphAnalysis(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load graph analysis');
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 0.6) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-orange-600 bg-orange-50 border-orange-200';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Internal Linking Analysis</h1>
        <p className="text-gray-600 mt-1">
          Optimize your internal linking structure with AI-powered recommendations
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'recommendations'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <LinkIcon className="w-4 h-4" />
              Link Recommendations
            </div>
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'analysis'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Graph Analysis
            </div>
          </button>
        </nav>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-medium">Error</div>
            <div className="text-sm mt-1">{error}</div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-primary-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Loading {activeTab}...</p>
          </div>
        </div>
      )}

      {/* Recommendations Tab */}
      {!isLoading && activeTab === 'recommendations' && (
        <div className="space-y-4">
          {recommendations.length === 0 ? (
            <div className="card text-center py-12">
              <LinkIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No recommendations found</h3>
              <p className="text-gray-600">
                Try crawling more pages or check back later.
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-gray-600">
                  Found <span className="font-semibold">{recommendations.length}</span> link opportunities
                </p>
                <button
                  onClick={loadRecommendations}
                  className="btn btn-secondary flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
              </div>

              {recommendations.map((rec, index) => (
                <div
                  key={index}
                  className="card hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      {/* Source Page (if available) */}
                      {rec.source_url && (
                        <div className="mb-3">
                          <span className="text-xs font-medium text-gray-500">From:</span>
                          <a
                            href={rec.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-gray-700 hover:text-primary-600 ml-2 inline-flex items-center gap-1"
                          >
                            {rec.source_url}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      )}

                      {/* Target Page */}
                      <div className="mb-3">
                        <span className="text-xs font-medium text-gray-500">Link to:</span>
                        <a
                          href={rec.target_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-base font-medium text-primary-600 hover:text-primary-700 ml-2 inline-flex items-center gap-1"
                        >
                          {rec.target_title}
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>

                      {/* Keyword */}
                      <div className="mb-3">
                        <span className="text-xs font-medium text-gray-500">On keyword:</span>
                        <span className="ml-2 px-2 py-1 bg-primary-50 text-primary-700 text-sm font-medium rounded">
                          {rec.keyword}
                        </span>
                      </div>

                      {/* Context */}
                      <div className="mb-2">
                        <span className="text-xs font-medium text-gray-500 block mb-1">Context:</span>
                        <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded border border-gray-200">
                          {rec.context}
                        </p>
                      </div>

                      {/* Reason */}
                      <div className="text-xs text-gray-500 italic">
                        {rec.reason}
                      </div>
                    </div>

                    {/* Score Badge */}
                    <div className="flex-shrink-0">
                      <div className={`px-3 py-2 rounded-lg border ${getScoreColor(rec.score)}`}>
                        <div className="text-xs font-medium">Score</div>
                        <div className="text-2xl font-bold">
                          {Math.round(rec.score * 100)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* Graph Analysis Tab */}
      {!isLoading && activeTab === 'analysis' && graphAnalysis && (
        <div className="space-y-6">
          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="text-sm text-gray-600 mb-1">Total Pages</div>
              <div className="text-3xl font-bold text-gray-900">{graphAnalysis.total_pages}</div>
            </div>
            <div className="card">
              <div className="text-sm text-gray-600 mb-1">Total Links</div>
              <div className="text-3xl font-bold text-gray-900">{graphAnalysis.total_links}</div>
            </div>
            <div className="card">
              <div className="text-sm text-gray-600 mb-1">Avg Links/Page</div>
              <div className="text-3xl font-bold text-gray-900">{graphAnalysis.avg_links_per_page}</div>
            </div>
            <div className="card">
              <div className="text-sm text-gray-600 mb-1">Orphan Pages</div>
              <div className="text-3xl font-bold text-red-600">{graphAnalysis.orphan_pages}</div>
            </div>
          </div>

          {/* Hub Pages */}
          {graphAnalysis.hub_pages.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Hub Pages (Most Outgoing Links)
              </h3>
              <div className="space-y-3">
                {graphAnalysis.hub_pages.map((page: any) => (
                  <div
                    key={page.page_id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex-1">
                      <a
                        href={page.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium text-gray-900 hover:text-primary-600 inline-flex items-center gap-2"
                      >
                        {page.title}
                        <ExternalLink className="w-4 h-4" />
                      </a>
                      <div className="text-sm text-gray-600 mt-1">
                        {page.out_degree} outgoing links • PageRank: {page.pagerank.toFixed(4)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500">SEO Score</div>
                      <div className="text-lg font-bold text-green-600">{Math.round(page.seo_score)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Authority Pages */}
          {graphAnalysis.authority_pages.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Authority Pages (Highest PageRank)
              </h3>
              <div className="space-y-3">
                {graphAnalysis.authority_pages.map((page: any) => (
                  <div
                    key={page.page_id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex-1">
                      <a
                        href={page.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium text-gray-900 hover:text-primary-600 inline-flex items-center gap-2"
                      >
                        {page.title}
                        <ExternalLink className="w-4 h-4" />
                      </a>
                      <div className="text-sm text-gray-600 mt-1">
                        {page.in_degree} incoming links • PageRank: {page.pagerank.toFixed(4)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500">SEO Score</div>
                      <div className="text-lg font-bold text-green-600">{Math.round(page.seo_score)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
