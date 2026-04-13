import { useState, useEffect } from 'react';
import { applicationsAPI } from '../api';

const STATUS_COLORS: Record<string, string> = {
  found: 'bg-gray-100 text-gray-700',
  saved: 'bg-blue-100 text-blue-700',
  tailoring: 'bg-yellow-100 text-yellow-700',
  ready: 'bg-green-100 text-green-700',
  submitted: 'bg-indigo-100 text-indigo-700',
  interviewing: 'bg-purple-100 text-purple-700',
  rejected: 'bg-red-100 text-red-700',
  offer: 'bg-emerald-100 text-emerald-700',
  closed: 'bg-gray-100 text-gray-500',
};

export default function Applications() {
  const [applications, setApplications] = useState<any[]>([]);
  const [pipeline, setPipeline] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    try {
      const res = await applicationsAPI.list();
      setApplications(res.data?.applications || []);
      setPipeline(res.data?.pipeline || {});
    } catch (err) {
      console.error('Failed to load applications', err);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (id: string, status: string) => {
    setUpdating(id);
    try {
      await applicationsAPI.update(id, { status });
      await loadApplications();
    } catch (err) {
      console.error('Failed to update', err);
    } finally {
      setUpdating(null);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Applications</h1>

      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <h2 className="font-semibold mb-3">Pipeline Overview</h2>
        <div className="flex flex-wrap gap-2">
          {Object.entries(pipeline).map(([status, count]) => (
            <span key={status} className={`px-3 py-1 rounded-full text-sm ${STATUS_COLORS[status] || 'bg-gray-100'}`}>
              {status}: {count}
            </span>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {applications.length === 0 ? (
          <p className="text-gray-500">No applications yet. Browse jobs and apply!</p>
        ) : (
          applications.map((app) => (
            <div key={app.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{app.job?.title || 'Unknown Position'}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_COLORS[app.status]}`}>
                      {app.status}
                    </span>
                  </div>
                  <p className="text-gray-600">{app.job?.company || 'Unknown Company'}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Applied: {app.applied_at ? new Date(app.applied_at).toLocaleDateString() : 'Not yet'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <select
                    value={app.status}
                    onChange={(e) => updateStatus(app.id, e.target.value)}
                    disabled={updating === app.id}
                    className="text-sm border border-gray-300 rounded px-2 py-1"
                  >
                    <option value="found">Found</option>
                    <option value="saved">Saved</option>
                    <option value="tailoring">Tailoring</option>
                    <option value="ready">Ready</option>
                    <option value="submitted">Submitted</option>
                    <option value="interviewing">Interviewing</option>
                    <option value="rejected">Rejected</option>
                    <option value="offer">Offer</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
