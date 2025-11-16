import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '@/lib/api';
import { Link as LinkIcon, TrendingUp, ExternalLink, AlertCircle, CheckCircle, RefreshCw, Search, Info, Filter } from 'lucide-react';

export default function InternalLinking() {
  const { id } = useParams<{ id: string }>();
  const projectId = parseInt(id || '0');

  const [activeTab, setActiveTab] = useState<'recommendations' | 'analysis'>('recommendations');
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [graphAnalysis, setGraphAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchFilter, setSearchFilter] = useState('');
  const [minScoreFilter, setMinScoreFilter] = useState(0);
  const [showFilters, setShowFilters] = useState(false);

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

  // Filter recommendations based on search and score
  const filteredRecommendations = recommendations.filter((rec) => {
    // Score filter
    if (rec.score < minScoreFilter / 100) return false;

    // Search filter (search in keyword, target title, source url, target url)
    if (searchFilter.trim()) {
      const search = searchFilter.toLowerCase();
      return (
        rec.keyword?.toLowerCase().includes(search) ||
        rec.target_title?.toLowerCase().includes(search) ||
        rec.target_url?.toLowerCase().includes(search) ||
        rec.source_url?.toLowerCase().includes(search)
      );
    }

    return true;
  });

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
                <div className="flex items-center gap-4">
                  <p className="text-sm text-gray-600">
                    Found <span className="font-semibold">{recommendations.length}</span> link opportunities
                    {(searchFilter || minScoreFilter > 0) && (
                      <span className="ml-2 text-primary-600">
                        ({filteredRecommendations.length} filtered)
                      </span>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowFilters(!showFilters)}
                    className={`btn btn-secondary flex items-center gap-2 ${showFilters ? 'bg-primary-50 text-primary-700' : ''}`}
                  >
                    <Filter className="w-4 h-4" />
                    {showFilters ? 'Hide Filters' : 'Show Filters'}
                  </button>
                  <button
                    onClick={loadRecommendations}
                    className="btn btn-secondary flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                  </button>
                </div>
              </div>

              {/* Filter Panel */}
              {showFilters && (
                <div className="card bg-gray-50 border-2 border-gray-300">
                  <div className="flex items-center gap-2 mb-4">
                    <Filter className="w-5 h-5 text-gray-700" />
                    <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Search Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Search (keyword, page, URL)
                      </label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                          type="text"
                          value={searchFilter}
                          onChange={(e) => setSearchFilter(e.target.value)}
                          placeholder="Search recommendations..."
                          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    {/* Score Filter */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Minimum Score: {minScoreFilter}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        step="5"
                        value={minScoreFilter}
                        onChange={(e) => setMinScoreFilter(parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                      </div>
                    </div>
                  </div>

                  {/* Reset Filters */}
                  {(searchFilter || minScoreFilter > 0) && (
                    <div className="mt-4 pt-4 border-t border-gray-300">
                      <button
                        onClick={() => {
                          setSearchFilter('');
                          setMinScoreFilter(0);
                        }}
                        className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                      >
                        Reset all filters
                      </button>
                    </div>
                  )}
                </div>
              )}

              {filteredRecommendations.length === 0 ? (
                <div className="card text-center py-12">
                  <Filter className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No recommendations match your filters</h3>
                  <p className="text-gray-600">
                    Try adjusting your search terms or minimum score.
                  </p>
                  <button
                    onClick={() => {
                      setSearchFilter('');
                      setMinScoreFilter(0);
                    }}
                    className="mt-4 btn btn-secondary"
                  >
                    Reset Filters
                  </button>
                </div>
              ) : (
                filteredRecommendations.map((rec, index) => (
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
                          <div className="ml-2">
                            <a
                              href={rec.target_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-base font-medium text-primary-600 hover:text-primary-700 inline-flex items-center gap-1"
                            >
                              {rec.target_title}
                              <ExternalLink className="w-4 h-4" />
                            </a>
                            <div className="text-xs text-gray-500 mt-1">{rec.target_url}</div>
                          </div>
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
                ))
              )}
            </>
          )}
        </div>
      )}

      {/* Graph Analysis Tab */}
      {!isLoading && activeTab === 'analysis' && graphAnalysis && (
        <div className="space-y-6">
          {/* Explanation Box */}
          <div className="card bg-blue-50 border-2 border-blue-200">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-blue-900 mb-2">Understanding Graph Analysis</h3>
                <p className="text-sm text-blue-800 mb-3">
                  Graph Analysis examines your site's internal linking structure to identify optimization opportunities.
                  It uses network analysis algorithms to measure how well your pages are connected.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div>
                    <strong className="text-blue-900">PageRank:</strong>
                    <span className="text-blue-800 ml-1">
                      Measures a page's importance based on the quality and quantity of links pointing to it. Higher is better.
                    </span>
                  </div>
                  <div>
                    <strong className="text-blue-900">Hub Pages:</strong>
                    <span className="text-blue-800 ml-1">
                      Pages with many outgoing links. These are great for navigation and distributing link equity.
                    </span>
                  </div>
                  <div>
                    <strong className="text-blue-900">Authority Pages:</strong>
                    <span className="text-blue-800 ml-1">
                      Pages with high PageRank. These are your most important content that receives many quality links.
                    </span>
                  </div>
                  <div>
                    <strong className="text-blue-900">Orphan Pages:</strong>
                    <span className="text-blue-800 ml-1">
                      Pages with no incoming internal links. These are hard to discover and should be linked from other pages.
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <div className="text-sm text-gray-600">Total Pages</div>
                <div className="group relative">
                  <Info className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                    Number of pages analyzed in your site's internal linking structure
                  </div>
                </div>
              </div>
              <div className="text-3xl font-bold text-gray-900">{graphAnalysis.total_pages}</div>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <div className="text-sm text-gray-600">Total Links</div>
                <div className="group relative">
                  <Info className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                    Total number of internal links between your pages
                  </div>
                </div>
              </div>
              <div className="text-3xl font-bold text-gray-900">{graphAnalysis.total_links}</div>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <div className="text-sm text-gray-600">Avg Links/Page</div>
                <div className="group relative">
                  <Info className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                    Average number of internal links per page. Aim for 3-10 for good internal linking.
                  </div>
                </div>
              </div>
              <div className="text-3xl font-bold text-gray-900">{graphAnalysis.avg_links_per_page}</div>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <div className="text-sm text-gray-600">Orphan Pages</div>
                <div className="group relative">
                  <Info className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                    Pages with no incoming links. These should be linked from other pages to improve discoverability.
                  </div>
                </div>
              </div>
              <div className="text-3xl font-bold text-red-600">{graphAnalysis.orphan_pages}</div>
            </div>
          </div>

          {/* Hub Pages */}
          {graphAnalysis.hub_pages.length > 0 && (
            <div className="card">
              <div className="flex items-start gap-2 mb-3">
                <h3 className="text-lg font-semibold text-gray-900">
                  Hub Pages (Most Outgoing Links)
                </h3>
                <div className="group relative">
                  <Info className="w-5 h-5 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-64 p-3 bg-gray-900 text-white text-xs rounded shadow-lg top-full left-0 mt-2">
                    Hub pages link to many other pages on your site. They're useful for navigation and distributing PageRank across your site. Consider making these pages accessible from your main navigation.
                  </div>
                </div>
              </div>
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
                      <div className="text-xs text-gray-500 mt-1">{page.url}</div>
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
              <div className="flex items-start gap-2 mb-3">
                <h3 className="text-lg font-semibold text-gray-900">
                  Authority Pages (Highest PageRank)
                </h3>
                <div className="group relative">
                  <Info className="w-5 h-5 text-gray-400 cursor-help" />
                  <div className="invisible group-hover:visible absolute z-10 w-64 p-3 bg-gray-900 text-white text-xs rounded shadow-lg top-full left-0 mt-2">
                    Authority pages have the highest PageRank scores, meaning they receive many quality internal links. These are your most important pages. Consider linking to conversion pages from these authorities to pass link equity.
                  </div>
                </div>
              </div>
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
                      <div className="text-xs text-gray-500 mt-1">{page.url}</div>
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
