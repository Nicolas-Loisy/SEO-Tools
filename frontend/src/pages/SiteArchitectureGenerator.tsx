import { useState } from 'react';
import { api } from '@/lib/api';
import { Loader2, TreePine, Globe, Search, Sparkles, ChevronDown, ChevronRight, Download } from 'lucide-react';

interface TreeNode {
  name: string;
  slug: string;
  keyword: string;
  title: string;
  meta_description: string;
  priority: string;
  level: number;
  target_word_count: number;
  children?: TreeNode[];
}

interface Cluster {
  id: number;
  keywords: string[];
  centroid: string;
}

interface ArchitectureResult {
  topic: string;
  language: string;
  total_keywords: number;
  num_clusters: number;
  depth: number;
  tree: TreeNode;
  clusters: Cluster[];
}

export default function SiteArchitectureGenerator() {
  const [topic, setTopic] = useState('');
  const [language, setLanguage] = useState('en');
  const [country, setCountry] = useState('us');
  const [depth, setDepth] = useState(3);
  const [numClusters, setNumClusters] = useState(5);
  const [maxKeywords, setMaxKeywords] = useState(100);
  const [provider, setProvider] = useState('openai');

  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<ArchitectureResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.generateSiteArchitecture({
        topic: topic.trim(),
        language,
        country,
        max_keywords: maxKeywords,
        num_clusters: numClusters,
        depth,
        provider,
      });

      setResult(data);

      // Auto-expand first level
      const firstLevelSlugs = data.tree.children?.map(c => c.slug) || [];
      setExpandedNodes(new Set(firstLevelSlugs));
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate architecture');
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleNode = (slug: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(slug)) {
      newExpanded.delete(slug);
    } else {
      newExpanded.add(slug);
    }
    setExpandedNodes(newExpanded);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const renderTree = (node: TreeNode, parentPath: string = '') => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedNodes.has(node.slug);
    const nodePath = parentPath + node.slug;

    return (
      <div key={nodePath} className="mb-2">
        <div className="flex items-start gap-2">
          {hasChildren && (
            <button
              onClick={() => toggleNode(node.slug)}
              className="mt-2 p-1 hover:bg-gray-100 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-600" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-600" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-6" />}

          <div className="flex-1 bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900">{node.name}</h3>
                  <span className={`text-xs px-2 py-1 rounded border ${getPriorityColor(node.priority)}`}>
                    {node.priority}
                  </span>
                </div>
                <p className="text-sm text-gray-600 font-mono">{node.slug}</p>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium text-gray-700">Keyword:</span>
                <span className="ml-2 text-gray-600">{node.keyword}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Title:</span>
                <span className="ml-2 text-gray-600">{node.title}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Meta:</span>
                <span className="ml-2 text-gray-600">{node.meta_description}</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Level: {node.level}</span>
                <span>Target: {node.target_word_count} words</span>
              </div>
            </div>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="ml-8 mt-2 space-y-2">
            {node.children!.map((child) => renderTree(child, nodePath))}
          </div>
        )}
      </div>
    );
  };

  const exportToJSON = () => {
    if (!result) return;

    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `${result.topic.replace(/\s+/g, '-')}-architecture.json`;
    link.click();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <TreePine className="w-8 h-8 text-green-600" />
            <h1 className="text-3xl font-bold text-gray-900">Site Architecture Generator</h1>
          </div>
          <p className="text-gray-600">
            Generate SEO-optimized site architecture using Google Autocomplete, K-means clustering, and LLM
          </p>
        </div>

        {/* Input Form */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Topic / Main Keyword *
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., digital marketing"
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="en">English</option>
                <option value="fr">French</option>
                <option value="es">Spanish</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Country
              </label>
              <div className="relative">
                <Globe className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <select
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="us">United States</option>
                  <option value="uk">United Kingdom</option>
                  <option value="fr">France</option>
                  <option value="de">Germany</option>
                  <option value="es">Spain</option>
                  <option value="ca">Canada</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                LLM Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tree Depth (1-5)
              </label>
              <input
                type="number"
                min="1"
                max="5"
                value={depth}
                onChange={(e) => setDepth(parseInt(e.target.value))}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Clusters (2-20)
              </label>
              <input
                type="number"
                min="2"
                max="20"
                value={numClusters}
                onChange={(e) => setNumClusters(parseInt(e.target.value))}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Keywords
              </label>
              <input
                type="number"
                min="10"
                max="500"
                value={maxKeywords}
                onChange={(e) => setMaxKeywords(parseInt(e.target.value))}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isGenerating || !topic.trim()}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating Architecture...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Site Architecture
              </>
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mb-6">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Summary</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">{result.total_keywords}</div>
                  <div className="text-sm text-gray-600 mt-1">Keywords Found</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-3xl font-bold text-green-600">{result.num_clusters}</div>
                  <div className="text-sm text-gray-600 mt-1">Semantic Clusters</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600">{result.depth}</div>
                  <div className="text-sm text-gray-600 mt-1">Tree Depth</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-3xl font-bold text-orange-600">
                    {result.tree.children?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">Main Categories</div>
                </div>
              </div>
            </div>

            {/* Clusters */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Keyword Clusters</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.clusters.map((cluster) => (
                  <div key={cluster.id} className="border rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">
                      Cluster {cluster.id + 1}: {cluster.centroid}
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {cluster.keywords.slice(0, 10).map((kw, idx) => (
                        <span
                          key={idx}
                          className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
                        >
                          {kw}
                        </span>
                      ))}
                      {cluster.keywords.length > 10 && (
                        <span className="text-xs px-2 py-1 text-gray-500">
                          +{cluster.keywords.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tree Structure */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Site Architecture Tree</h2>
                <button
                  onClick={exportToJSON}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Export JSON
                </button>
              </div>

              <div className="space-y-2">
                {renderTree(result.tree)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
