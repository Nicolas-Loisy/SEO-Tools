import { useState } from 'react';
import { api } from '@/lib/api';
import { Key } from 'lucide-react';

interface LoginProps {
  onLogin: () => void;
}

export default function Login({ onLogin }: LoginProps) {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      api.setApiKey(apiKey);
      // Test the API key by fetching quota
      await api.getQuota();
      onLogin();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid API key. Please check and try again.');
      api.clearApiKey();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary-900 mb-2">SEO SaaS Tool</h1>
          <p className="text-primary-700">Enter your API key to continue</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="label">
                <Key className="w-4 h-4 inline mr-2" />
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk_test_..."
                className="input"
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                Your API key is stored locally and never sent to our servers
              </p>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary w-full"
            >
              {isLoading ? 'Verifying...' : 'Login'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-600 text-center">
              Don't have an API key?{' '}
              <a href="#" className="text-primary-600 hover:text-primary-700 font-medium">
                Generate one
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
