import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { FileText, Sparkles, CheckCircle, AlertCircle, Loader2, Copy, Download } from 'lucide-react';

export default function SEOContentGenerator() {
  const [activeTab, setActiveTab] = useState<'generate' | 'optimize' | 'validate'>('generate');
  const [templates, setTemplates] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate tab state
  const [keyword, setKeyword] = useState('');
  const [pageType, setPageType] = useState('article');
  const [tone, setTone] = useState('professional');
  const [length, setLength] = useState(1000);
  const [language, setLanguage] = useState('en');
  const [context, setContext] = useState('');
  const [provider, setProvider] = useState('openai');
  const [generatedContent, setGeneratedContent] = useState<any>(null);

  // Optimize tab state
  const [contentToOptimize, setContentToOptimize] = useState('');
  const [optimizeKeyword, setOptimizeKeyword] = useState('');
  const [optimizePageType, setOptimizePageType] = useState('article');
  const [optimizedResult, setOptimizedResult] = useState<any>(null);

  // Validate tab state
  const [contentToValidate, setContentToValidate] = useState('');
  const [validateKeyword, setValidateKeyword] = useState('');
  const [metaTitle, setMetaTitle] = useState('');
  const [metaDescription, setMetaDescription] = useState('');
  const [validationResult, setValidationResult] = useState<any>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await api.getContentTemplates();
      setTemplates(data);
      if (data.page_types && data.page_types.length > 0) {
        setPageType(data.page_types[0].value);
        setOptimizePageType(data.page_types[0].value);
      }
      if (data.tones && data.tones.length > 0) {
        setTone(data.tones[0].value);
      }
    } catch (err: any) {
      console.error('Failed to load templates:', err);
    }
  };

  const handleGenerate = async () => {
    if (!keyword.trim()) {
      setError('Please enter a keyword');
      return;
    }

    setIsLoading(true);
    setError(null);
    setGeneratedContent(null);

    try {
      const result = await api.generateSEOContent({
        keyword: keyword.trim(),
        page_type: pageType,
        tone,
        length,
        language,
        context: context.trim() || undefined,
        provider,
      });

      setGeneratedContent(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate content');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!contentToOptimize.trim() || !optimizeKeyword.trim()) {
      setError('Please enter both content and keyword');
      return;
    }

    setIsLoading(true);
    setError(null);
    setOptimizedResult(null);

    try {
      const result = await api.optimizeSEOContent({
        content: contentToOptimize.trim(),
        keyword: optimizeKeyword.trim(),
        page_type: optimizePageType,
        language,
        provider,
      });

      setOptimizedResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to optimize content');
    } finally {
      setIsLoading(false);
    }
  };

  const handleValidate = async () => {
    if (!contentToValidate.trim() || !validateKeyword.trim()) {
      setError('Please enter both content and keyword');
      return;
    }

    setIsLoading(true);
    setError(null);
    setValidationResult(null);

    try {
      const result = await api.validateSEOContent({
        content: contentToValidate.trim(),
        keyword: validateKeyword.trim(),
        meta_title: metaTitle.trim() || undefined,
        meta_description: metaDescription.trim() || undefined,
      });

      setValidationResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to validate content');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">SEO Content Generator</h1>
          </div>
          <p className="text-gray-600">
            Generate, optimize, and validate SEO-friendly content using AI
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('generate')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'generate'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Generate Content
                </div>
              </button>
              <button
                onClick={() => setActiveTab('optimize')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'optimize'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Optimize Content
                </div>
              </button>
              <button
                onClick={() => setActiveTab('validate')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'validate'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Validate Content
                </div>
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Generate Tab */}
            {activeTab === 'generate' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Keyword *
                    </label>
                    <input
                      type="text"
                      value={keyword}
                      onChange={(e) => setKeyword(e.target.value)}
                      placeholder="e.g., digital marketing"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Page Type
                    </label>
                    <select
                      value={pageType}
                      onChange={(e) => setPageType(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {templates?.page_types?.map((type: any) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Content Tone
                    </label>
                    <select
                      value={tone}
                      onChange={(e) => setTone(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {templates?.tones?.map((t: any) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Word Count: {length}
                    </label>
                    <input
                      type="range"
                      min="300"
                      max="3000"
                      step="100"
                      value={length}
                      onChange={(e) => setLength(parseInt(e.target.value))}
                      className="w-full"
                    />
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
                      <option value="fr">Français</option>
                      <option value="es">Español</option>
                      <option value="de">Deutsch</option>
                    </select>
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

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Additional Context (Optional)
                  </label>
                  <textarea
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="Any specific requirements or additional information..."
                    rows={3}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  onClick={handleGenerate}
                  disabled={isLoading || !keyword.trim()}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Generate SEO Content
                    </>
                  )}
                </button>

                {/* Generated Content Display */}
                {generatedContent && (
                  <div className="mt-6 space-y-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <span className="font-semibold text-green-800">Content Generated Successfully!</span>
                      </div>
                      <p className="text-sm text-green-700">
                        Word count: {generatedContent.word_count} words
                      </p>
                    </div>

                    <div className="bg-white border rounded-lg p-6 space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold text-gray-900">Title (H1)</h3>
                          <button
                            onClick={() => copyToClipboard(generatedContent.title)}
                            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                          >
                            <Copy className="w-4 h-4" />
                            Copy
                          </button>
                        </div>
                        <p className="text-lg font-bold text-gray-800">{generatedContent.title}</p>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold text-gray-900">Meta Title</h3>
                          <button
                            onClick={() => copyToClipboard(generatedContent.meta_title)}
                            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                          >
                            <Copy className="w-4 h-4" />
                            Copy
                          </button>
                        </div>
                        <p className="text-gray-700">{generatedContent.meta_title}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {generatedContent.meta_title?.length || 0} characters
                        </p>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold text-gray-900">Meta Description</h3>
                          <button
                            onClick={() => copyToClipboard(generatedContent.meta_description)}
                            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                          >
                            <Copy className="w-4 h-4" />
                            Copy
                          </button>
                        </div>
                        <p className="text-gray-700">{generatedContent.meta_description}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {generatedContent.meta_description?.length || 0} characters
                        </p>
                      </div>

                      <div>
                        <h3 className="font-semibold text-gray-900 mb-2">Introduction</h3>
                        <p className="text-gray-700 whitespace-pre-wrap">{generatedContent.introduction}</p>
                      </div>

                      {generatedContent.sections && generatedContent.sections.length > 0 && (
                        <div>
                          <h3 className="font-semibold text-gray-900 mb-3">Content Sections</h3>
                          <div className="space-y-4">
                            {generatedContent.sections.map((section: any, idx: number) => (
                              <div key={idx} className="border-l-4 border-blue-500 pl-4">
                                <h4 className="font-semibold text-gray-800 mb-2">{section.heading}</h4>
                                {section.subheadings && section.subheadings.length > 0 && (
                                  <ul className="list-disc list-inside mb-2 text-sm text-gray-600">
                                    {section.subheadings.map((sub: string, subIdx: number) => (
                                      <li key={subIdx}>{sub}</li>
                                    ))}
                                  </ul>
                                )}
                                <p className="text-gray-700 whitespace-pre-wrap">{section.content}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {generatedContent.conclusion && (
                        <div>
                          <h3 className="font-semibold text-gray-900 mb-2">Conclusion</h3>
                          <p className="text-gray-700 whitespace-pre-wrap">{generatedContent.conclusion}</p>
                        </div>
                      )}

                      {generatedContent.cta && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h3 className="font-semibold text-blue-900 mb-2">Call-to-Action</h3>
                          <p className="text-blue-800">{generatedContent.cta}</p>
                        </div>
                      )}

                      {generatedContent.keywords_used && generatedContent.keywords_used.length > 0 && (
                        <div>
                          <h3 className="font-semibold text-gray-900 mb-2">Keywords Used</h3>
                          <div className="flex flex-wrap gap-2">
                            {generatedContent.keywords_used.map((kw: string, idx: number) => (
                              <span key={idx} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                                {kw}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Optimize Tab */}
            {activeTab === 'optimize' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Keyword *
                    </label>
                    <input
                      type="text"
                      value={optimizeKeyword}
                      onChange={(e) => setOptimizeKeyword(e.target.value)}
                      placeholder="e.g., digital marketing"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Page Type
                    </label>
                    <select
                      value={optimizePageType}
                      onChange={(e) => setOptimizePageType(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {templates?.page_types?.map((type: any) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content to Optimize *
                  </label>
                  <textarea
                    value={contentToOptimize}
                    onChange={(e) => setContentToOptimize(e.target.value)}
                    placeholder="Paste your existing content here..."
                    rows={12}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  />
                </div>

                <button
                  onClick={handleOptimize}
                  disabled={isLoading || !contentToOptimize.trim() || !optimizeKeyword.trim()}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Optimizing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Optimize Content
                    </>
                  )}
                </button>

                {optimizedResult && (
                  <div className="mt-6 space-y-4">
                    <div className="bg-white border rounded-lg p-6">
                      <h3 className="font-semibold text-gray-900 mb-4">Optimization Results</h3>

                      {optimizedResult.improvements && optimizedResult.improvements.length > 0 && (
                        <div className="mb-4">
                          <h4 className="font-medium text-gray-800 mb-2">Improvements Made</h4>
                          <ul className="list-disc list-inside space-y-1 text-gray-700">
                            {optimizedResult.improvements.map((imp: string, idx: number) => (
                              <li key={idx}>{imp}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {optimizedResult.suggestions && optimizedResult.suggestions.length > 0 && (
                        <div className="mb-4">
                          <h4 className="font-medium text-gray-800 mb-2">Suggestions</h4>
                          <ul className="list-disc list-inside space-y-1 text-gray-700">
                            {optimizedResult.suggestions.map((sug: string, idx: number) => (
                              <li key={idx}>{sug}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {optimizedResult.optimized_content && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-gray-800">Optimized Content</h4>
                            <button
                              onClick={() => copyToClipboard(optimizedResult.optimized_content)}
                              className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                            >
                              <Copy className="w-4 h-4" />
                              Copy
                            </button>
                          </div>
                          <div className="bg-gray-50 border rounded-lg p-4">
                            <p className="text-gray-700 whitespace-pre-wrap">{optimizedResult.optimized_content}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Validate Tab */}
            {activeTab === 'validate' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Keyword *
                    </label>
                    <input
                      type="text"
                      value={validateKeyword}
                      onChange={(e) => setValidateKeyword(e.target.value)}
                      placeholder="e.g., digital marketing"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Meta Title (Optional)
                    </label>
                    <input
                      type="text"
                      value={metaTitle}
                      onChange={(e) => setMetaTitle(e.target.value)}
                      placeholder="Your meta title..."
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Meta Description (Optional)
                    </label>
                    <input
                      type="text"
                      value={metaDescription}
                      onChange={(e) => setMetaDescription(e.target.value)}
                      placeholder="Your meta description..."
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content to Validate *
                  </label>
                  <textarea
                    value={contentToValidate}
                    onChange={(e) => setContentToValidate(e.target.value)}
                    placeholder="Paste your content here..."
                    rows={12}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  />
                </div>

                <button
                  onClick={handleValidate}
                  disabled={isLoading || !contentToValidate.trim() || !validateKeyword.trim()}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Validating...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      Validate Content
                    </>
                  )}
                </button>

                {validationResult && (
                  <div className="mt-6 space-y-4">
                    <div className={`text-center p-6 rounded-lg border-2 ${
                      validationResult.score >= 80 ? 'bg-green-50 border-green-300' :
                      validationResult.score >= 60 ? 'bg-yellow-50 border-yellow-300' :
                      'bg-red-50 border-red-300'
                    }`}>
                      <div className={`text-5xl font-bold mb-2 ${getScoreColor(validationResult.score)}`}>
                        {validationResult.score}
                      </div>
                      <div className="text-sm font-medium text-gray-700">SEO Score</div>
                    </div>

                    {validationResult.metrics && (
                      <div className="bg-white border rounded-lg p-6">
                        <h3 className="font-semibold text-gray-900 mb-4">Metrics</h3>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                          {Object.entries(validationResult.metrics).map(([key, value]: [string, any]) => (
                            <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
                              <div className="text-xl font-bold text-gray-800">{value}</div>
                              <div className="text-xs text-gray-600 mt-1">
                                {key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {validationResult.issues && validationResult.issues.length > 0 && (
                      <div className="bg-white border rounded-lg p-6">
                        <h3 className="font-semibold text-gray-900 mb-4">Issues Found</h3>
                        <div className="space-y-2">
                          {validationResult.issues.map((issue: any, idx: number) => (
                            <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg border ${getSeverityColor(issue.severity)}`}>
                              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                              <div>
                                <div className="font-medium">{issue.message}</div>
                                <div className="text-xs mt-1 opacity-80">Type: {issue.type}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {validationResult.suggestions && validationResult.suggestions.length > 0 && (
                      <div className="bg-white border rounded-lg p-6">
                        <h3 className="font-semibold text-gray-900 mb-4">Suggestions</h3>
                        <ul className="space-y-2">
                          {validationResult.suggestions.map((suggestion: string, idx: number) => (
                            <li key={idx} className="flex items-start gap-2">
                              <CheckCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                              <span className="text-gray-700">{suggestion}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
