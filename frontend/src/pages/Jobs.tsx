import { useState, useEffect } from 'react';
import { jobsAPI, applicationsAPI, tailoringAPI } from '../api';

export default function Jobs() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [applyingTo, setApplyingTo] = useState<string | null>(null);
  const [tailoring, setTailoring] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      const res = await jobsAPI.list();
      setJobs(res.data?.jobs || []);
    } catch (err) {
      console.error('Failed to load jobs', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return loadJobs();
    setLoading(true);
    try {
      const res = await jobsAPI.search({ q: searchTerm });
      setJobs(res.data?.jobs || []);
    } catch (err) {
      console.error('Search failed', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (jobId: string) => {
    setApplyingTo(jobId);
    try {
      await applicationsAPI.create(jobId);
      alert('Application created!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create application');
    } finally {
      setApplyingTo(null);
    }
  };

  const handleTailor = async (jobId: string) => {
    setTailoring(jobId);
    try {
      const res = await tailoringAPI.tailor(jobId, undefined, false);
      setResult(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate tailored content');
    } finally {
      setTailoring(null);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Jobs</h1>

      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search jobs..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md"
        />
        <button type="submit" className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
          Search
        </button>
      </form>

      {result && (
        <div className="mb-6 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold">Tailored Content</h3>
            <button onClick={() => setResult(null)} className="text-gray-500 hover:text-gray-700">Close</button>
          </div>
          
          {result.cover_letter && (
            <div className="mb-4">
              <h4 className="font-medium mb-2">Cover Letter</h4>
              <div className="bg-gray-50 p-4 rounded whitespace-pre-wrap text-sm">
                {result.cover_letter.full_text}
              </div>
            </div>
          )}
          
          {result.resume?.summary_suggestion && (
            <div>
              <h4 className="font-medium mb-2">Suggested Summary</h4>
              <p className="bg-gray-50 p-4 rounded text-sm">{result.resume.summary_suggestion}</p>
            </div>
          )}
        </div>
      )}

      <div className="space-y-4">
        {jobs.length === 0 ? (
          <p className="text-gray-500">No jobs found. Add job sources to start discovering opportunities!</p>
        ) : (
          jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex justify-between">
                <div>
                  <h3 className="font-semibold text-lg">{job.title}</h3>
                  <p className="text-gray-600">{job.company}</p>
                  <div className="flex gap-4 mt-2 text-sm text-gray-500">
                    {job.location && <span>{job.location}</span>}
                    {job.remote_type && <span>{job.remote_type}</span>}
                    {job.employment_type && <span>{job.employment_type}</span>}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleTailor(job.id)}
                    disabled={tailoring === job.id}
                    className="px-4 py-2 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
                  >
                    {tailoring === job.id ? 'Generating...' : 'Tailor'}
                  </button>
                  <button
                    onClick={() => handleApply(job.id)}
                    disabled={applyingTo === job.id}
                    className="px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {applyingTo === job.id ? 'Applying...' : 'Apply'}
                  </button>
                </div>
              </div>
              {job.description && (
                <p className="mt-3 text-sm text-gray-600 line-clamp-3">{job.description}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
