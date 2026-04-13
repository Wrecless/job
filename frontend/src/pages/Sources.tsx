import { useState, useEffect } from 'react';
import { sourcesAPI } from '../api';

export default function Sources() {
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({
    name: '',
    source_type: 'greenhouse',
    base_url: '',
  });
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const res = await sourcesAPI.list();
      setSources(res.data || []);
    } catch (err) {
      console.error('Failed to load sources', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);
    setMessage('');
    try {
      await sourcesAPI.create(form);
      setForm({ name: '', source_type: 'greenhouse', base_url: '' });
      await loadSources();
      setMessage('Source added!');
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to add source');
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete ${name}?`)) return;
    try {
      await sourcesAPI.delete(name);
      await loadSources();
    } catch (err) {
      console.error('Delete failed', err);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Job Sources</h1>

      {message && (
        <div className={`mb-4 p-3 rounded ${message.includes('added') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {message}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="font-semibold mb-4">Add Job Source</h2>
        <form onSubmit={handleAdd} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="My Company Jobs"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                value={form.source_type}
                onChange={(e) => setForm({ ...form, source_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="greenhouse">Greenhouse</option>
                <option value="lever">Lever</option>
                <option value="ashby">Ashby</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
            <input
              type="url"
              value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              placeholder="https://boards.greenhouse.io/companyname"
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              The main board URL from your job board's careers page
            </p>
          </div>
          <button
            type="submit"
            disabled={adding}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {adding ? 'Adding...' : 'Add Source'}
          </button>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow">
        <h2 className="font-semibold p-4 border-b">Your Job Sources</h2>
        {sources.length === 0 ? (
          <p className="p-4 text-gray-500">No job sources added yet.</p>
        ) : (
          <ul className="divide-y">
            {sources.map((source) => (
              <li key={source.id} className="p-4 flex justify-between items-center">
                <div>
                  <p className="font-medium">{source.name}</p>
                  <p className="text-sm text-gray-500">
                    {source.source_type} - {source.base_url}
                  </p>
                  <div className="flex gap-4 mt-1 text-xs text-gray-400">
                    <span>Active: {source.is_active ? 'Yes' : 'No'}</span>
                    <span>Jobs: {source.job_count || 0}</span>
                    {source.last_fetch_at && (
                      <span>Last fetch: {new Date(source.last_fetch_at).toLocaleString()}</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(source.name)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
