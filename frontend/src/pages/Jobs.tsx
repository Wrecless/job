import { isAxiosError } from 'axios';
import { useEffect, useMemo, useState } from 'react';
import { alertsAPI, applicationsAPI, botAPI, jobsAPI, sourcesAPI } from '../api';

type ViewFilter = 'all' | 'applied' | 'not_applied';
type AlertTab = 'unread' | 'ready';

type Job = {
  job_id: string;
  title: string;
  company: string;
  source_name: string;
  source_url: string;
  application_url: string;
  location?: string | null;
  remote_type?: string | null;
  score_total?: number | null;
  description?: string | null;
};

type Application = {
  id: string;
  job_id: string;
  status?: string | null;
};

type AlertDraftData = {
  ready_to_review?: boolean;
  score_total?: number;
  reason?: string;
  application_draft?: string;
  job_summary?: {
    company?: string;
    title?: string;
    location?: string | null;
    application_url?: string;
  };
  next_steps?: string[];
};

type Alert = {
  id: string;
  job_title: string;
  job_company: string;
  job_location?: string | null;
  status: 'unread' | 'read' | 'ready' | string;
  explanation: string;
  draft_data?: AlertDraftData;
};

type Source = {
  id: string;
  name: string;
  source_type: string;
  base_url: string;
  is_active: boolean;
  error_count: number;
};

function getErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError(err)) {
    return err.response?.data?.detail || fallback;
  }

  return fallback;
}

function LinkPill({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-sm font-medium text-cyan-100 transition hover:bg-cyan-400/20 hover:text-white"
    >
      {label}
    </a>
  );
}

const PLACEHOLDER_HOSTS = new Set(['example.com', 'localhost', '127.0.0.1']);

function normalizeExternalLink(href: string | undefined): string | null {
  if (!href) return null;

  try {
    const url = new URL(href);
    if (PLACEHOLDER_HOSTS.has(url.hostname)) return null;
    return href;
  } catch {
    return null;
  }
}

function LinkChip({ href, label, mutedLabel }: { href: string | null; label: string; mutedLabel: string }) {
  if (!href) {
    return (
      <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm font-medium text-slate-500">
        {mutedLabel}
      </span>
    );
  }

  return <LinkPill href={href} label={label} />;
}

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [unreadAlerts, setUnreadAlerts] = useState(0);
  const [readyAlerts, setReadyAlerts] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<ViewFilter>('all');
  const [alertTab, setAlertTab] = useState<AlertTab>('unread');
  const [busyJobId, setBusyJobId] = useState<string | null>(null);
  const [busyAlertId, setBusyAlertId] = useState<string | null>(null);
  const [busyBot, setBusyBot] = useState(false);
  const [busySourceId, setBusySourceId] = useState<string | null>(null);
  const [sourceName, setSourceName] = useState('');
  const [sourceType, setSourceType] = useState('greenhouse');
  const [sourceBaseUrl, setSourceBaseUrl] = useState('');
  const [sourceIsActive, setSourceIsActive] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      const [jobsRes, appsRes, alertsRes, sourcesRes] = await Promise.all([
        jobsAPI.list(),
        applicationsAPI.list(),
        alertsAPI.list(),
        sourcesAPI.list(),
      ]);

      setJobs(jobsRes.data?.jobs || []);
      setApplications(appsRes.data?.applications || []);
      setAlerts(alertsRes.data?.alerts || []);
      setSources(sourcesRes.data?.sources || []);
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
  const hasPlaceholderLinks = jobs.some(
    (job) => !normalizeExternalLink(job.source_url) || !normalizeExternalLink(job.application_url),
  );

  const handleToggleApplied = async (job: Job) => {
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
    } catch (err: unknown) {
      setMessage(getErrorMessage(err, 'Failed to update application status'));
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
    } catch (err: unknown) {
      setMessage(getErrorMessage(err, 'Failed to update alert'));
    } finally {
      setBusyAlertId(null);
    }
  };

  const handleCopyDraft = async (alert: Alert) => {
    if (!alert.draft_data?.application_draft) return;

    try {
      await navigator.clipboard.writeText(alert.draft_data.application_draft);
      await alertsAPI.updateStatus(alert.id, 'ready');
      setMessage(`Copied draft and marked ${alert.job_title} as ready`);
      await loadJobs();
    } catch (err: unknown) {
      setMessage(getErrorMessage(err, 'Failed to copy draft'));
    }
  };

  const handleRunBot = async () => {
    setBusyBot(true);
    setMessage('');

    try {
      const response = await botAPI.run();
      const result = response.data;
      setMessage(
        `Bot ran: checked ${result.sources_checked} sources, skipped ${result.sources_skipped}, created ${result.jobs_created} jobs, updated ${result.jobs_updated}, scored ${result.jobs_scored}.`,
      );
      await loadJobs();
    } catch (err: unknown) {
      setMessage(getErrorMessage(err, 'Failed to run bot'));
    } finally {
      setBusyBot(false);
    }
  };

  const handleCreateSource = async () => {
    setBusySourceId('create');
    setMessage('');

    try {
      await sourcesAPI.create({
        name: sourceName,
        source_type: sourceType,
        base_url: sourceBaseUrl,
        is_active: sourceIsActive,
      });
      setSourceName('');
      setSourceType('greenhouse');
      setSourceBaseUrl('');
      setSourceIsActive(true);
      setMessage('Source added');
      await loadJobs();
    } catch (err: unknown) {
      setMessage(getErrorMessage(err, 'Failed to add source'));
    } finally {
      setBusySourceId(null);
    }
  };

  const handleToggleSource = async (source: Source) => {
    setBusySourceId(source.id);
    setMessage('');

    try {
      await sourcesAPI.update(source.id, { is_active: !source.is_active });
      setMessage(`${source.name} ${source.is_active ? 'disabled' : 'enabled'}`);
      await loadJobs();
    } catch (err: unknown) {
      setMessage(getErrorMessage(err, 'Failed to update source'));
    } finally {
      setBusySourceId(null);
    }
  };

  const handleDeleteSource = async (source: Source) => {
    setBusySourceId(source.id);
    setMessage('');

    try {
      await sourcesAPI.delete(source.id);
      setMessage(`Deleted ${source.name}`);
      await loadJobs();
    } catch (err: unknown) {
      setMessage(getErrorMessage(err, 'Failed to delete source'));
    } finally {
      setBusySourceId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#05060a] px-6 py-12 text-slate-100">
        <div className="mx-auto max-w-6xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_34%),linear-gradient(180deg,#05060a_0%,#090b12_100%)] px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30 backdrop-blur">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-cyan-300/80">Job view</p>
              <h1 className="mt-2 text-4xl font-semibold tracking-tight text-white sm:text-5xl">Jobs</h1>
              <p className="mt-3 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
                Clear, high-contrast cards with bigger spacing and simpler labels.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm sm:min-w-[22rem]">
              <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3">
                <div className="text-slate-400">Applied</div>
                <div className="mt-1 text-2xl font-semibold text-white">{appliedCount}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3">
                <div className="text-slate-400">Open</div>
                <div className="mt-1 text-2xl font-semibold text-white">{notAppliedCount}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3">
                <div className="text-slate-400">Matches</div>
                <div className="mt-1 text-2xl font-semibold text-white">{unreadAlerts + readyAlerts}</div>
              </div>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-2">
            {(['all', 'applied', 'not_applied'] as const).map((value) => (
              <button
                key={value}
                onClick={() => setFilter(value)}
                className={`rounded-full px-4 py-2 text-sm font-medium tracking-wide transition ${
                  filter === value
                    ? 'bg-cyan-300 text-black'
                    : 'border border-white/15 bg-black/25 text-slate-200 hover:bg-white/10'
                }`}
              >
                {value.replace('_', ' ')}
              </button>
            ))}

            <button
              onClick={handleRunBot}
              disabled={busyBot}
              className="ml-auto rounded-full border border-cyan-300/30 bg-cyan-300 px-4 py-2 text-sm font-semibold text-black transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busyBot ? 'Finding jobs...' : 'Find and score jobs'}
            </button>
          </div>

          {message && <div className="mt-4 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-cyan-50">{message}</div>}

          {hasPlaceholderLinks && (
            <div className="mt-4 rounded-2xl border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-amber-100">
              Some configured sources still point at demo URLs. Real links will appear once real job sources are added.
            </div>
          )}
        </header>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.65fr)]">
          <section className="space-y-4">
            {visibleJobs.length === 0 ? (
              <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-slate-300">
                No jobs to show for this filter.
              </div>
            ) : (
              visibleJobs.map((job) => {
                const application = applicationsByJobId.get(job.job_id);
                const applied = Boolean(application);

                return (
                  <article
                    key={job.job_id}
                    className="rounded-3xl border border-white/10 bg-[#0b1020]/95 p-6 shadow-xl shadow-black/30"
                  >
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${applied ? 'bg-emerald-400/15 text-emerald-200' : 'bg-slate-500/15 text-slate-300'}`}>
                            {applied ? 'Applied' : 'Not applied'}
                          </span>
                          {job.score_total != null && (
                            <span className="rounded-full bg-cyan-400/15 px-3 py-1 text-xs font-semibold text-cyan-100">
                              Score {Number(job.score_total).toFixed(1)}
                            </span>
                          )}
                        </div>

                        <h2 className="mt-4 text-2xl font-semibold leading-tight text-white">{job.title}</h2>
                        <p className="mt-1 text-lg text-slate-300">{job.company}</p>

                        <div className="mt-4 flex flex-wrap gap-2 text-sm text-slate-300">
                          {job.location && <span className="rounded-full bg-white/5 px-3 py-1">{job.location}</span>}
                          {job.remote_type && <span className="rounded-full bg-white/5 px-3 py-1">{job.remote_type}</span>}
                          <span className="rounded-full bg-white/5 px-3 py-1">Found on {job.source_name}</span>
                        </div>

                        <div className="mt-5 flex flex-wrap gap-3">
                          <LinkChip
                            href={normalizeExternalLink(job.source_url)}
                            label="Open source"
                            mutedLabel="Open source unavailable"
                          />
                          <LinkChip
                            href={normalizeExternalLink(job.application_url)}
                            label="Direct link"
                            mutedLabel="Direct link unavailable"
                          />
                        </div>

                        {job.description && (
                          <p className="mt-5 max-w-4xl text-base leading-7 text-slate-300 line-clamp-4">
                            {job.description}
                          </p>
                        )}
                      </div>

                      <button
                        onClick={() => handleToggleApplied(job)}
                        disabled={busyJobId === job.job_id}
                        className="inline-flex items-center justify-center rounded-full bg-cyan-300 px-5 py-3 text-sm font-semibold text-black transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {busyJobId === job.job_id ? 'Saving...' : applied ? 'Mark not applied' : 'Mark applied'}
                      </button>
                    </div>

                    {application?.status && (
                      <p className="mt-4 text-sm text-slate-400">Status: {application.status}</p>
                    )}
                  </article>
                );
              })
            )}
          </section>

          <aside className="space-y-6 xl:sticky xl:top-6 xl:self-start">
            <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-semibold text-white">Match queue</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => setAlertTab('unread')}
                    className={`rounded-full px-3 py-1 text-sm font-medium ${alertTab === 'unread' ? 'bg-cyan-300 text-black' : 'bg-white/10 text-slate-200'}`}
                  >
                    Unread ({unreadAlerts})
                  </button>
                  <button
                    onClick={() => setAlertTab('ready')}
                    className={`rounded-full px-3 py-1 text-sm font-medium ${alertTab === 'ready' ? 'bg-amber-300 text-black' : 'bg-white/10 text-slate-200'}`}
                  >
                    Ready ({readyAlerts})
                  </button>
                </div>
              </div>

              {(alertTab === 'unread' ? unreadAlertsList : readyAlertsList).length === 0 ? (
                <p className="mt-4 text-sm leading-6 text-slate-400">No {alertTab} matches yet.</p>
              ) : (
                <div className="mt-4 space-y-4">
                  {(alertTab === 'unread' ? unreadAlertsList : readyAlertsList).map((alert) => (
                    <article key={alert.id} className="rounded-2xl border border-white/10 bg-black/25 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-white">{alert.job_title}</p>
                          <p className="text-sm text-slate-300">{alert.job_company}</p>
                          <p className="mt-1 text-sm text-slate-400">{alert.job_location || 'Remote'}</p>
                        </div>
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${alert.status === 'ready' ? 'bg-amber-300/15 text-amber-100' : alert.status === 'read' ? 'bg-white/10 text-slate-300' : 'bg-emerald-400/15 text-emerald-100'}`}>
                          {alert.status}
                        </span>
                      </div>

                      <p className="mt-3 text-sm leading-6 text-slate-300">{alert.explanation}</p>

                      <div className="mt-4 flex flex-wrap gap-2">
                        {alert.draft_data?.application_draft && (
                          <button
                            onClick={() => handleCopyDraft(alert)}
                            className="rounded-full bg-white px-3 py-2 text-xs font-semibold text-black transition hover:bg-slate-200"
                          >
                            Copy & ready
                          </button>
                        )}
                        {alert.status !== 'read' && (
                          <button
                            onClick={() => handleMarkAlertRead(alert.id)}
                            disabled={busyAlertId === alert.id}
                            className="rounded-full border border-white/15 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-100 transition hover:bg-white/10 disabled:opacity-50"
                          >
                            {busyAlertId === alert.id ? 'Saving...' : 'Mark read'}
                          </button>
                        )}
                      </div>

                      {alert.draft_data?.next_steps && (
                        <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-300">
                          {alert.draft_data.next_steps.map((step: string) => (
                            <li key={step} className="rounded-xl bg-white/5 px-3 py-2">
                              {step}
                            </li>
                          ))}
                        </ul>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <h2 className="text-lg font-semibold text-white">Sources</h2>
              <p className="mt-1 text-sm leading-6 text-slate-400">
                Add real job boards here. Manual sources are stored, but only Greenhouse, Lever, and Ashby are fetched by the bot.
              </p>

              <div className="mt-4 space-y-3">
                <input
                  value={sourceName}
                  onChange={(event) => setSourceName(event.target.value)}
                  placeholder="Source name"
                  className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-slate-500"
                />
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <select
                    value={sourceType}
                    onChange={(event) => setSourceType(event.target.value)}
                    className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white"
                  >
                    <option value="greenhouse">greenhouse</option>
                    <option value="lever">lever</option>
                    <option value="ashby">ashby</option>
                    <option value="manual">manual</option>
                  </select>
                  <input
                    value={sourceBaseUrl}
                    onChange={(event) => setSourceBaseUrl(event.target.value)}
                    placeholder="Base URL"
                    className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-slate-500"
                  />
                </div>
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={sourceIsActive}
                    onChange={(event) => setSourceIsActive(event.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-black/30"
                  />
                  Active
                </label>
                <button
                  onClick={handleCreateSource}
                  disabled={busySourceId === 'create' || !sourceName || !sourceType || !sourceBaseUrl}
                  className="rounded-full bg-cyan-300 px-4 py-2 text-sm font-semibold text-black transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busySourceId === 'create' ? 'Saving...' : 'Add source'}
                </button>
              </div>

              <div className="mt-5 space-y-3">
                {sources.length === 0 ? (
                  <p className="text-sm text-slate-400">No sources yet.</p>
                ) : (
                  sources.map((source) => (
                    <article key={source.id} className="rounded-2xl border border-white/10 bg-black/25 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-white">{source.name}</p>
                          <p className="text-sm text-slate-300">{source.source_type}</p>
                          <p className="mt-1 break-all text-xs text-slate-500">{source.base_url}</p>
                        </div>
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${source.is_active ? 'bg-emerald-400/15 text-emerald-100' : 'bg-white/10 text-slate-400'}`}>
                          {source.is_active ? 'active' : 'inactive'}
                        </span>
                      </div>

                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          onClick={() => handleToggleSource(source)}
                          disabled={busySourceId === source.id}
                          className="rounded-full border border-white/15 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-100 transition hover:bg-white/10 disabled:opacity-50"
                        >
                          {busySourceId === source.id ? 'Saving...' : source.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          onClick={() => handleDeleteSource(source)}
                          disabled={busySourceId === source.id}
                          className="rounded-full border border-rose-300/20 bg-rose-300/10 px-3 py-2 text-xs font-semibold text-rose-100 transition hover:bg-rose-300/20 disabled:opacity-50"
                        >
                          Delete
                        </button>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
