import { useEffect, useMemo, useState } from 'react';
import { alertsAPI, applicationsAPI, jobsAPI } from '../api';

type ViewFilter = 'all' | 'applied' | 'not_applied';
type AlertTab = 'unread' | 'ready';

export default function Jobs() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [unreadAlerts, setUnreadAlerts] = useState(0);
  const [readyAlerts, setReadyAlerts] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<ViewFilter>('all');
  const [alertTab, setAlertTab] = useState<AlertTab>('unread');
  const [busyJobId, setBusyJobId] = useState<string | null>(null);
  const [busyAlertId, setBusyAlertId] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      const [jobsRes, appsRes, alertsRes] = await Promise.all([
        jobsAPI.list(),
        applicationsAPI.list(),
        alertsAPI.list(),
      ]);

      setJobs(jobsRes.data?.jobs || []);
      setApplications(appsRes.data?.applications || []);
      setAlerts(alertsRes.data?.alerts || []);
      setUnreadAlerts(alertsRes.data?.unread_total || 0);
      setReadyAlerts(alertsRes.data?.ready_total || 0);
    } catch (err) {
      console.error('Failed to load jobs', err);
    } finally {
      setLoading(false);
    }
  };

  const applicationsByJobId = useMemo(
    () => new Map(applications.map((application) => [application.job_id, application])),
    [applications],
  );

  const visibleJobs = jobs.filter((job) => {
    const isApplied = applicationsByJobId.has(job.job_id);
    if (filter === 'applied') return isApplied;
    if (filter === 'not_applied') return !isApplied;
    return true;
  });

  const appliedCount = applications.length;
  const notAppliedCount = jobs.length - applicationsByJobId.size;

  const unreadAlertsList = alerts.filter((alert) => alert.status !== 'ready');
  const readyAlertsList = alerts.filter((alert) => alert.status === 'ready');

  const handleToggleApplied = async (job: any) => {
    const existing = applicationsByJobId.get(job.job_id);
    setBusyJobId(job.job_id);
    setMessage('');

    try {
      if (existing) {
        await applicationsAPI.delete(existing.id);
        setMessage(`Removed applied status for ${job.title}`);
      } else {
        await applicationsAPI.create(job.job_id);
        setMessage(`Marked ${job.title} as applied`);
      }

      await loadJobs();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to update application status');
    } finally {
      setBusyJobId(null);
    }
  };

  const handleMarkAlertRead = async (alertId: string) => {
    setBusyAlertId(alertId);
    setMessage('');

    try {
      await alertsAPI.markRead(alertId);
      await loadJobs();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to update alert');
    } finally {
      setBusyAlertId(null);
    }
  };

  const handleCopyDraft = async (alert: any) => {
    if (!alert.draft_data?.application_draft) return;

    try {
      await navigator.clipboard.writeText(alert.draft_data.application_draft);
      await alertsAPI.updateStatus(alert.id, 'ready');
      setMessage(`Copied draft and marked ${alert.job_title} as ready`);
      await loadJobs();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to copy draft');
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Jobs</h1>
            <p className="mt-1 text-gray-600">
              {appliedCount} applied, {notAppliedCount} not applied
            </p>
            <p className="mt-1 text-sm text-indigo-700">{unreadAlerts} new matches</p>
          </div>

          <div className="flex gap-2">
            {(['all', 'applied', 'not_applied'] as const).map((value) => (
              <button
                key={value}
                onClick={() => setFilter(value)}
                className={`rounded-md px-4 py-2 text-sm capitalize ${
                  filter === value ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700'
                }`}
              >
                {value.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {message && <div className="mb-4 rounded bg-blue-50 px-4 py-3 text-blue-800">{message}</div>}

        <div className="mb-6 rounded-lg border border-indigo-100 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Match queue</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setAlertTab('unread')}
                className={`rounded-md px-3 py-1 text-sm ${alertTab === 'unread' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700'}`}
              >
                Unread ({unreadAlerts})
              </button>
              <button
                onClick={() => setAlertTab('ready')}
                className={`rounded-md px-3 py-1 text-sm ${alertTab === 'ready' ? 'bg-amber-600 text-white' : 'bg-gray-100 text-gray-700'}`}
              >
                Ready ({readyAlerts})
              </button>
            </div>
          </div>
          {(alertTab === 'unread' ? unreadAlertsList : readyAlertsList).length === 0 ? (
            <p className="mt-2 text-sm text-gray-500">No {alertTab} matches yet.</p>
          ) : (
            <div className="mt-3 space-y-3">
              {(alertTab === 'unread' ? unreadAlertsList : readyAlertsList).map((alert) => (
                <div key={alert.id} className="rounded-md border border-gray-200 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{alert.job_title} at {alert.job_company}</p>
                      <p className="text-sm text-gray-600">{alert.job_location || 'Remote'}</p>
                      <p className="mt-1 text-sm text-gray-700">{alert.explanation}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2 py-1 text-xs ${alert.status === 'ready' ? 'bg-amber-100 text-amber-700' : alert.status === 'read' ? 'bg-gray-100 text-gray-600' : 'bg-green-100 text-green-700'}`}>
                        {alert.status}
                      </span>
                      {alert.draft_data?.application_draft && (
                        <button
                          onClick={() => handleCopyDraft(alert)}
                          className="rounded-md bg-gray-900 px-3 py-1 text-xs text-white"
                        >
                          Copy & ready
                        </button>
                      )}
                      {alert.status !== 'read' && (
                        <button
                          onClick={() => handleMarkAlertRead(alert.id)}
                          disabled={busyAlertId === alert.id}
                          className="rounded-md bg-indigo-600 px-3 py-1 text-xs text-white disabled:opacity-50"
                        >
                          {busyAlertId === alert.id ? 'Saving...' : 'Mark read'}
                        </button>
                      )}
                      
                    </div>
                  </div>
                  {alert.draft_data?.next_steps && (
                    <ul className="mt-2 list-disc pl-5 text-sm text-gray-600">
                      {alert.draft_data.next_steps.map((step: string) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ul>
                  )}
                  {alert.draft_data?.application_draft && (
                    <pre className="mt-3 whitespace-pre-wrap rounded bg-gray-50 p-3 text-sm text-gray-700">
                      {alert.draft_data.application_draft}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          {visibleJobs.length === 0 ? (
            <p className="text-gray-500">No jobs to show.</p>
          ) : (
            visibleJobs.map((job) => {
              const application = applicationsByJobId.get(job.job_id);
              const applied = Boolean(application);

              return (
                <div key={job.job_id} className="rounded-lg bg-white p-4 shadow">
                  <div className="flex justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold">{job.title}</h3>
                      <p className="text-gray-600">{job.company}</p>
                      <div className="mt-2 flex gap-4 text-sm text-gray-500">
                        {job.location && <span>{job.location}</span>}
                        {job.remote_type && <span>{job.remote_type}</span>}
                        {job.score_total != null && <span>Score {Number(job.score_total).toFixed(1)}</span>}
                      </div>
                    </div>

                    <button
                      onClick={() => handleToggleApplied(job)}
                      disabled={busyJobId === job.job_id}
                      className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {busyJobId === job.job_id ? 'Saving...' : applied ? 'Mark not applied' : 'Mark applied'}
                    </button>
                  </div>

                  {job.description && <p className="mt-3 text-sm text-gray-600 line-clamp-3">{job.description}</p>}

                  <div className="mt-3 flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-1 text-xs ${
                        applied ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {applied ? 'Applied' : 'Not applied'}
                    </span>
                    {application?.status && (
                      <span className="text-xs text-gray-500">Status: {application.status}</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
