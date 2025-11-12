import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { api } from "@/lib/api";
import type { Page } from "@/types";

interface DetectedSchema {
  page_id: number;
  url: string;
  title: string;
  detected_types: string[];
}

interface GeneratedSchema {
  page_id: number;
  schema_type: string;
  schema: Record<string, any>;
  html: string;
  validation: {
    valid: boolean;
    errors: string[];
    warnings: string[];
  };
}

export default function StructuredData() {
  const { id } = useParams<{ id: string }>();
  const projectId = parseInt(id || "0");

  const [detectedSchemas, setDetectedSchemas] = useState<DetectedSchema[]>([]);
  const [selectedPage, setSelectedPage] = useState<DetectedSchema | null>(null);
  const [selectedSchemaType, setSelectedSchemaType] = useState<string>("");
  const [generatedSchema, setGeneratedSchema] = useState<GeneratedSchema | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isBulkDetecting, setIsBulkDetecting] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [aiImprovements, setAiImprovements] = useState<string[]>([]);
  const [aiRecommendations, setAiRecommendations] = useState<string[]>([]);

  const handleBulkDetect = async () => {
    try {
      setIsBulkDetecting(true);
      setError(null);
      const result = await api.bulkDetectSchemas(projectId, 50);
      setDetectedSchemas(result.pages);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to detect schemas");
    } finally {
      setIsBulkDetecting(false);
    }
  };

  const handlePageSelect = (page: DetectedSchema) => {
    setSelectedPage(page);
    setGeneratedSchema(null);
    if (page.detected_types.length > 0) {
      setSelectedSchemaType(page.detected_types[0]);
    }
  };

  const handleGenerateSchema = async () => {
    if (!selectedPage || !selectedSchemaType) return;

    try {
      setIsLoading(true);
      setError(null);
      const result = await api.generateJSONLD(
        projectId,
        selectedPage.page_id,
        selectedSchemaType
      );
      setGeneratedSchema(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate schema");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyToClipboard = () => {
    if (!generatedSchema) return;

    navigator.clipboard.writeText(generatedSchema.html);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyJSON = () => {
    if (!generatedSchema) return;

    navigator.clipboard.writeText(JSON.stringify(generatedSchema.schema, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleEnhanceWithAI = async () => {
    if (!selectedPage || !generatedSchema) return;

    try {
      setIsEnhancing(true);
      setError(null);
      setAiImprovements([]);
      setAiRecommendations([]);

      const result = await api.enhanceSchemaWithAI(
        projectId,
        selectedPage.page_id,
        generatedSchema.schema,
        'openai' // Can be made configurable
      );

      // Update the schema with enhanced version
      setGeneratedSchema({
        ...generatedSchema,
        schema: result.enhanced_schema,
        html: formatSchemaAsHTML(result.enhanced_schema),
      });

      setAiImprovements(result.improvements || []);
      setAiRecommendations(result.recommendations || []);

    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to enhance schema with AI");
    } finally {
      setIsEnhancing(false);
    }
  };

  const formatSchemaAsHTML = (schema: Record<string, any>): string => {
    const jsonStr = JSON.stringify(schema, null, 2);
    return `<script type="application/ld+json">\n${jsonStr}\n</script>`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Structured Data</h1>
          <p className="mt-2 text-gray-600">
            Generate and validate Schema.org JSON-LD markup for your pages
          </p>
        </div>
        <button
          onClick={handleBulkDetect}
          disabled={isBulkDetecting}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isBulkDetecting ? "Detecting..." : "Detect Schemas"}
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pages List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow">
            <div className="px-4 py-3 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Pages ({detectedSchemas.length})
              </h2>
            </div>
            <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
              {detectedSchemas.length === 0 ? (
                <div className="px-4 py-8 text-center text-gray-500">
                  <p>No schemas detected yet.</p>
                  <p className="text-sm mt-2">
                    Click "Detect Schemas" to analyze your pages.
                  </p>
                </div>
              ) : (
                detectedSchemas.map((page) => (
                  <button
                    key={page.page_id}
                    onClick={() => handlePageSelect(page)}
                    className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors ${
                      selectedPage?.page_id === page.page_id
                        ? "bg-primary-50 border-l-4 border-primary-600"
                        : ""
                    }`}
                  >
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {page.title || "Untitled"}
                    </div>
                    <div className="text-xs text-gray-500 truncate mt-1">
                      {page.url}
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {page.detected_types.map((type) => (
                        <span
                          key={type}
                          className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                        >
                          {type}
                        </span>
                      ))}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Schema Generator */}
        <div className="lg:col-span-2">
          {selectedPage ? (
            <div className="space-y-4">
              {/* Schema Type Selection */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Generate Schema
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Selected Page
                    </label>
                    <div className="text-sm text-gray-900">
                      {selectedPage.title}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {selectedPage.url}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Schema Type
                    </label>
                    <select
                      value={selectedSchemaType}
                      onChange={(e) => setSelectedSchemaType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      {selectedPage.detected_types.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    onClick={handleGenerateSchema}
                    disabled={isLoading || !selectedSchemaType}
                    className="w-full px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? "Generating..." : "Generate JSON-LD"}
                  </button>
                </div>
              </div>

              {/* Generated Schema */}
              {generatedSchema && (
                <>
                  {/* Validation Results */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Validation
                    </h3>

                    <div className="space-y-3">
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-700 mr-2">
                          Status:
                        </span>
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            generatedSchema.validation.valid
                              ? "bg-green-100 text-green-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {generatedSchema.validation.valid ? "Valid" : "Invalid"}
                        </span>
                      </div>

                      {generatedSchema.validation.errors.length > 0 && (
                        <div>
                          <div className="text-sm font-medium text-red-700 mb-2">
                            Errors:
                          </div>
                          <ul className="list-disc list-inside space-y-1">
                            {generatedSchema.validation.errors.map((error, idx) => (
                              <li key={idx} className="text-sm text-red-600">
                                {error}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {generatedSchema.validation.warnings.length > 0 && (
                        <div>
                          <div className="text-sm font-medium text-yellow-700 mb-2">
                            Warnings:
                          </div>
                          <ul className="list-disc list-inside space-y-1">
                            {generatedSchema.validation.warnings.map(
                              (warning, idx) => (
                                <li key={idx} className="text-sm text-yellow-600">
                                  {warning}
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* AI Enhancement Section */}
                  {(aiImprovements.length > 0 || aiRecommendations.length > 0) && (
                    <div className="bg-white rounded-lg shadow p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        ✨ AI Enhancements
                      </h3>

                      {aiImprovements.length > 0 && (
                        <div className="mb-4">
                          <div className="text-sm font-medium text-green-700 mb-2">
                            Improvements Made:
                          </div>
                          <ul className="list-disc list-inside space-y-1">
                            {aiImprovements.map((improvement, idx) => (
                              <li key={idx} className="text-sm text-gray-700">
                                {improvement}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {aiRecommendations.length > 0 && (
                        <div>
                          <div className="text-sm font-medium text-blue-700 mb-2">
                            SEO Recommendations:
                          </div>
                          <ul className="list-disc list-inside space-y-1">
                            {aiRecommendations.map((rec, idx) => (
                              <li key={idx} className="text-sm text-gray-700">
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* JSON-LD Output */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">
                        Generated JSON-LD
                      </h3>
                      <div className="flex gap-2">
                        <button
                          onClick={handleEnhanceWithAI}
                          disabled={isEnhancing}
                          className="px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                        >
                          {isEnhancing ? (
                            <>
                              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              Enhancing...
                            </>
                          ) : (
                            <>✨ AI Enhance</>
                          )}
                        </button>
                        <button
                          onClick={handleCopyJSON}
                          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                        >
                          {copied ? "Copied!" : "Copy JSON"}
                        </button>
                        <button
                          onClick={handleCopyToClipboard}
                          className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
                        >
                          {copied ? "Copied!" : "Copy HTML"}
                        </button>
                      </div>
                    </div>

                    <pre className="bg-gray-50 p-4 rounded border border-gray-200 overflow-x-auto text-xs">
                      <code>{generatedSchema.html}</code>
                    </pre>

                    <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                      <p className="text-sm text-blue-800">
                        <strong>💡 How to use:</strong> Copy the HTML code above
                        and paste it into the <code>&lt;head&gt;</code> section of
                        your page.
                      </p>
                    </div>
                  </div>

                  {/* Schema Preview */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Schema Preview
                    </h3>
                    <pre className="bg-gray-50 p-4 rounded border border-gray-200 overflow-x-auto text-xs">
                      <code>
                        {JSON.stringify(generatedSchema.schema, null, 2)}
                      </code>
                    </pre>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="text-gray-400 mb-4">
                <svg
                  className="mx-auto h-12 w-12"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No page selected
              </h3>
              <p className="text-gray-500">
                Select a page from the list to generate structured data
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
