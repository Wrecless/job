import { useState, useEffect } from 'react';
import { profileAPI, applicationsAPI, jobsAPI } from '../api';

export default function Dashboard() {
  const [stats, setStats] = useState({
    profileComplete: false,
    applicationsCount: 0,
    jobsCount: 0,
    pendingTasks: 0,
    pipeline: {} as Record<string, number>,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [profileRes, appsRes, jobsRes, tasksRes] = await Promise.all([
        profileAPI.get().catch(() => ({ data: null })),
        applicationsAPI.list().catch(() => ({ data: { total: 0, applications: [], pipeline: {} } })),
        jobsAPI.list().catch(() => ({ data: { total: 0 } })),
        applicationsAPI.tasks().catch(() => ({ data: [] })),
      ]);

      setStats({
        profileComplete: !!profileRes.data?.headline,
        applicationsCount: appsRes.data?.total || 0,
        jobsCount: jobsRes.data?.total || 0,
        pendingTasks: tasksRes.data?.length || 0,
        pipeline: appsRes.data?.pipeline || {},
      });
    } catch (err) {
      console.error('Failed to load stats', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard title="Profile" value={stats.profileComplete ? 'Complete' : 'Incomplete'} />
        <StatCard title="Applications" value={stats.applicationsCount.toString()} />
        <StatCard title="Jobs" value={stats.jobsCount.toString()} />
        <StatCard title="Pending Tasks" value={stats.pendingTasks.toString()} />
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Application Pipeline</h2>
        {Object.keys(stats.pipeline).length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.pipeline).map(([status, count]) => (
              <span key={status} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                {status}: {count}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No applications yet. Start by adding job sources!</p>
        )}
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 mb-2">Getting Started</h3>
        <ol className="list-decimal list-inside text-blue-700 space-y-1 text-sm">
          <li>Complete your profile with target roles and locations</li>
          <li>Upload your resume</li>
          <li>Add job sources (Greenhouse, Lever, Ashby)</li>
          <li>Match jobs to your profile</li>
          <li>Apply and track your applications</li>
        </ol>
      </div>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
