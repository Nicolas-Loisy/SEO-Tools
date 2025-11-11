import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Search as SearchIcon, Filter, ExternalLink, X, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [processingTime, setProcessingTime] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [reindexMessage, setReindexMessage] = useState<string>('');
  const [stats, setStats] = useState<any>(null);

  // Filters
  const [statusCode, setStatusCode] = useState<string>('');
  const [minSeoScore, setMinSeoScore] = useState<string>('');
  const [maxSeoScore, setMaxSeoScore] = useState<string>('');
  const [minWordCount, setMinWordCount] = useState<string>('');

  // Load stats on mount
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await api.getSearchStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load search stats:', error);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      const params: any = { q: query };

      if (statusCode) params.status_code = parseInt(statusCode);
      if (minSeoScore) params.min_seo_score = parseFloat(minSeoScore);
      if (maxSeoScore) params.max_seo_score = parseFloat(maxSeoScore);
      if (minWordCount) params.min_word_count = parseInt(minWordCount);

      const data = await api.searchPages(params);
      setResults(data.hits);
      setTotal(data.total);
      setProcessingTime(data.processing_time_ms);
    } catch (error: any) {
      console.error('Search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearFilters = () => {
    setStatusCode('');
    setMinSeoScore('');
    setMaxSeoScore('');
    setMinWordCount('');
  };

  const handleReindex = async () => {
    setIsReindexing(true);
    setReindexMessage('');
    try {
      const result = await api.reindexPages();
      setReindexMessage(result.message);
      // Reload stats after reindexing
      await loadStats();
      setTimeout(() => setReindexMessage(''), 5000);
    } catch (error: any) {
      setReindexMessage('Error during reindexing: ' + (error.message || 'Unknown error'));
      setTimeout(() => setReindexMessage(''), 5000);
    } finally {
      setIsReindexing(false);
    }
  };

  const getSEOScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 70) return 'text-blue-600 bg-blue-50';
    if (score >= 50) return 'text-yellow-600 bg-yellow-50';
    if (score >= 30) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const highlightText = (text: string) => {
    // Meilisearch returns highlighted text with <mark> tags
    return { __html: text };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Search Pages</h1>
          <p className="text-gray-600 mt-1">
            Search through all crawled pages with full-text search
          </p>
        </div>
        <button
          onClick={handleReindex}
          disabled={isReindexing}
          className="btn btn-secondary flex items-center gap-2"
          title="Reindex all pages in Meilisearch"
        >
          <RefreshCw className={`w-4 h-4 ${isReindexing ? 'animate-spin' : ''}`} />
          {isReindexing ? 'Reindexing...' : 'Reindex Pages'}
        </button>
      </div>

      {/* Index Status */}
      {stats && (
        <div className={`p-4 rounded-lg flex items-start gap-3 ${
          stats.status === 'healthy'
            ? 'bg-green-50 border border-green-200'
            : stats.status === 'error'
            ? 'bg-red-50 border border-red-200'
            : 'bg-yellow-50 border border-yellow-200'
        }`}>
          {stats.status === 'healthy' ? (
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          )}
          <div className="flex-1">
            <div className={`font-medium ${
              stats.status === 'healthy' ? 'text-green-900' : 'text-red-900'
            }`}>
              Search Index Status: {stats.status === 'healthy' ? 'Healthy' : stats.status}
            </div>
            <div className={`text-sm mt-1 ${
              stats.status === 'healthy' ? 'text-green-700' : 'text-red-700'
            }`}>
              {stats.error ? (
                <span>Error: {stats.error}</span>
              ) : (
                <span>
                  {stats.number_of_documents.toLocaleString()} pages indexed
                  {stats.is_indexing && ' (indexing in progress...)'}
                  {stats.number_of_documents === 0 && (
                    <span className="block mt-1 font-medium">
                      Click "Reindex Pages" to index your existing pages
                    </span>
                  )}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Reindex Message */}
      {reindexMessage && (
        <div className={`p-4 rounded-lg ${
          reindexMessage.includes('Error') || reindexMessage.includes('error')
            ? 'bg-red-50 text-red-800 border border-red-200'
            : 'bg-green-50 text-green-800 border border-green-200'
        }`}>
          {reindexMessage}
        </div>
      )}

      {/* Search Form */}
      <div className="card">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search in titles, descriptions, content..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`btn ${showFilters ? 'btn-primary' : 'btn-secondary'} flex items-center gap-2`}
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>
            <button
              type="submit"
              disabled={!query.trim() || isLoading}
              className="btn btn-primary px-8"
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status Code
                </label>
                <input
                  type="number"
                  value={statusCode}
                  onChange={(e) => setStatusCode(e.target.value)}
                  placeholder="e.g., 200"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Min SEO Score
                </label>
                <input
                  type="number"
                  value={minSeoScore}
                  onChange={(e) => setMinSeoScore(e.target.value)}
                  placeholder="0-100"
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max SEO Score
                </label>
                <input
                  type="number"
                  value={maxSeoScore}
                  onChange={(e) => setMaxSeoScore(e.target.value)}
                  placeholder="0-100"
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Min Word Count
                </label>
                <input
                  type="number"
                  value={minWordCount}
                  onChange={(e) => setMinWordCount(e.target.value)}
                  placeholder="e.g., 300"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="md:col-span-2 lg:col-span-4 flex justify-end">
                <button
                  type="button"
                  onClick={clearFilters}
                  className="btn btn-secondary flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  Clear Filters
                </button>
              </div>
            </div>
          )}
        </form>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Search Results</h2>
              <p className="text-sm text-gray-600 mt-1">
                Found {total.toLocaleString()} results in {processingTime}ms
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {results.map((result) => (
              <div
                key={result.id}
                className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {/* URL */}
                    <div className="flex items-center gap-2 mb-2">
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary-600 hover:text-primary-700 truncate flex items-center gap-1"
                      >
                        {result.url}
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                    </div>

                    {/* Title (highlighted) */}
                    {result._formatted?.title && (
                      <h3
                        className="text-lg font-medium text-gray-900 mb-2"
                        dangerouslySetInnerHTML={highlightText(result._formatted.title)}
                      />
                    )}

                    {/* Meta Description (highlighted) */}
                    {result._formatted?.meta_description && (
                      <p
                        className="text-sm text-gray-600 mb-3 line-clamp-2"
                        dangerouslySetInnerHTML={highlightText(result._formatted.meta_description)}
                      />
                    )}

                    {/* Content Snippet (highlighted) */}
                    {result._formatted?.text_content && (
                      <p
                        className="text-sm text-gray-500 line-clamp-2"
                        dangerouslySetInnerHTML={highlightText(result._formatted.text_content)}
                      />
                    )}

                    {/* Metadata */}
                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                      {result.status_code && (
                        <span>Status: {result.status_code}</span>
                      )}
                      {result.word_count !== undefined && (
                        <span>{result.word_count} words</span>
                      )}
                      {result.internal_links_count !== undefined && (
                        <span>{result.internal_links_count} internal links</span>
                      )}
                    </div>
                  </div>

                  {/* SEO Score Badge */}
                  {result.seo_score !== undefined && (
                    <div className="flex-shrink-0">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSEOScoreColor(result.seo_score)}`}>
                        {Math.round(result.seo_score)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && results.length === 0 && query && (
        <div className="card text-center py-12">
          <SearchIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600">
            Try adjusting your search query or filters
          </p>
        </div>
      )}
    </div>
  );
}
