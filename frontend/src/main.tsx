import React, { FormEvent, useMemo, useState } from 'react';
import ReactDOM from 'react-dom/client';
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import {
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { api } from './lib/api';
import './styles.css';

const qc = new QueryClient();

type Source = {
  id: number;
  url: string;
  title: string;
  state: string;
  cadence_minutes: number;
  max_videos: number;
  discovery_mode: string;
  failure_count: number;
};

type LibraryItem = {
  article_id: number;
  title: string;
  version: number;
  body_preview: string;
  video_item_id: number;
};

type Job = {
  id: number;
  type: string;
  status: string;
  source_id?: number;
  video_item_id?: number;
  error?: string;
  created_at: string;
};
type ItemTransition = {
  id: number;
  from_status: string;
  to_status: string;
  message: string;
  created_at: string;
};

type Collection = { id: number; name: string };

function Page({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className='page'>
      <h1>{title}</h1>
      {children}
    </section>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className='card stat'>
      <p className='label'>{label}</p>
      <p className='value'>{value}</p>
    </article>
  );
}

function Home() {
  const sources = useQuery({ queryKey: ['sources'], queryFn: async () => (await api.get('/sources')).data as Source[] });
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: async () => (await api.get('/jobs')).data as Job[] });
  const library = useQuery({ queryKey: ['library', ''], queryFn: async () => (await api.get('/library')).data as LibraryItem[] });

  const failedJobs = (jobs.data ?? []).filter((j) => j.status.includes('fail')).length;

  return (
    <Page title='Dashboard'>
      <div className='grid'>
        <StatCard label='Sources' value={sources.data?.length ?? 0} />
        <StatCard label='Articles' value={library.data?.length ?? 0} />
        <StatCard label='Jobs queued / running' value={(jobs.data ?? []).filter((j) => ['queued', 'running'].includes(j.status)).length} />
        <StatCard label='Failed jobs' value={failedJobs} />
      </div>
      <article className='card'>
        <h2>Recent articles</h2>
        <ul className='stack'>
          {(library.data ?? []).slice(0, 6).map((item) => (
            <li key={item.article_id}>
              <Link to={`/reader/${item.article_id}`}>{item.title}</Link>
            </li>
          ))}
        </ul>
      </article>
    </Page>
  );
}

function Sources() {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const sources = useQuery({ queryKey: ['sources'], queryFn: async () => (await api.get('/sources')).data as Source[] });

  const createSource = useMutation({
    mutationFn: async () => api.post('/sources', { title, url }),
    onSuccess: () => {
      setTitle('');
      setUrl('');
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });

  const updateSource = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Source> }) => api.patch(`/sources/${id}`, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sources'] }),
  });

  const refreshSource = useMutation({
    mutationFn: async (id: number) => api.post(`/sources/${id}/refresh`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    createSource.mutate();
  };

  return (
    <Page title='Sources'>
      <article className='card'>
        <h2>Add source</h2>
        <form className='row' onSubmit={onSubmit}>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder='Display title (optional)' />
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder='YouTube channel URL' required />
          <button disabled={createSource.isPending}>{createSource.isPending ? 'Adding...' : 'Add source'}</button>
        </form>
      </article>

      <div className='stack'>
        {(sources.data ?? []).map((src) => (
          <article className='card' key={src.id}>
            <h3>{src.title || src.url}</h3>
            <p className='muted'>{src.url}</p>
            <div className='row'>
              <label>
                State
                <select
                  value={src.state}
                  onChange={(e) => updateSource.mutate({ id: src.id, payload: { state: e.target.value } })}
                >
                  <option value='enabled'>Enabled</option>
                  <option value='paused'>Paused</option>
                  <option value='archived'>Archived</option>
                </select>
              </label>
              <label>
                Cadence (min)
                <input
                  type='number'
                  min={5}
                  defaultValue={src.cadence_minutes}
                  onBlur={(e) => updateSource.mutate({ id: src.id, payload: { cadence_minutes: Number(e.target.value) } })}
                />
              </label>
              <label>
                Max videos
                <input
                  type='number'
                  min={1}
                  defaultValue={src.max_videos}
                  onBlur={(e) => updateSource.mutate({ id: src.id, payload: { max_videos: Number(e.target.value) } })}
                />
              </label>
            </div>
            <div className='row space-between'>
              <p className='muted'>Failures: {src.failure_count}</p>
              <button onClick={() => refreshSource.mutate(src.id)}>Refresh now</button>
            </div>
          </article>
        ))}
      </div>
    </Page>
  );
}

function Jobs() {
  const queryClient = useQueryClient();
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: async () => (await api.get('/jobs')).data as Job[] });

  const retry = useMutation({
    mutationFn: async (id: number) => api.post(`/jobs/${id}/retry`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  return (
    <Page title='Jobs'>
      <article className='card'>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Status</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {(jobs.data ?? []).map((job) => (
              <tr key={job.id}>
                <td>{job.id}</td>
                <td>{job.type}</td>
                <td>{job.status}</td>
                <td>{new Date(job.created_at).toLocaleString()}</td>
                <td>
                  {job.status.includes('fail') ? (
                    <button onClick={() => retry.mutate(job.id)} disabled={retry.isPending}>Retry</button>
                  ) : (
                    <span className='muted'>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </Page>
  );
}

function Library() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  const library = useQuery({
    queryKey: ['library', q],
    queryFn: async () => (await api.get('/library', { params: q ? { q } : {} })).data as LibraryItem[],
  });

  return (
    <Page title='Library'>
      <article className='card'>
        <input
          placeholder='Search by title...'
          defaultValue={q}
          onChange={(e) => setParams(e.target.value ? { q: e.target.value } : {})}
        />
      </article>
      <div className='grid'>
        {(library.data ?? []).map((item) => (
          <article key={item.article_id} className='card'>
            <h3>{item.title}</h3>
            <p className='muted'>Version {item.version}</p>
            <p>{item.body_preview || 'No preview available.'}</p>
            <Link to={`/reader/${item.article_id}`}>Open reader</Link>
          </article>
        ))}
      </div>
    </Page>
  );
}

function Reader() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);

  const detail = useQuery({
    queryKey: ['article', id],
    queryFn: async () => (await api.get(`/articles/${id}`)).data,
    enabled: Boolean(id),
  });

  const regenerate = useMutation({
    mutationFn: async () => api.post(`/articles/${id}/regenerate`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['article', id] }),
  });
  const timeline = useQuery({
    queryKey: ['item-timeline', detail.data?.id, detail.data?.video_item_id],
    queryFn: async () => (await api.get(`/items/${detail.data?.video_item_id}/timeline`)).data as ItemTransition[],
    enabled: Boolean(detail.data?.video_item_id),
  });

  const version = useMemo(() => {
    const versions = detail.data?.versions ?? [];
    if (!versions.length) return null;
    if (selectedVersion) return versions.find((v: any) => v.version === selectedVersion) ?? versions[0];
    return versions[0];
  }, [detail.data, selectedVersion]);

  return (
    <Page title='Reader'>
      <article className='card'>
        <h2>{detail.data?.title ?? 'Loading...'}</h2>
        <div className='row space-between'>
          <label>
            Version
            <select
              value={version?.version ?? ''}
              onChange={(e) => setSelectedVersion(Number(e.target.value))}
              disabled={!detail.data?.versions?.length}
            >
              {(detail.data?.versions ?? []).map((v: any) => (
                <option key={v.version} value={v.version}>
                  v{v.version}
                </option>
              ))}
            </select>
          </label>
          <button onClick={() => regenerate.mutate()} disabled={regenerate.isPending}>
            {regenerate.isPending ? 'Regenerating...' : 'Regenerate article'}
          </button>
        </div>
      </article>

      <article className='card reader'>
        <pre>{version?.body ?? 'No content available.'}</pre>
      </article>
      <article className='card'>
        <h3>Processing timeline</h3>
        <ul className='stack'>
          {(timeline.data ?? []).map((t) => (
            <li key={t.id}>
              <strong>{t.to_status}</strong> <span className='muted'>{new Date(t.created_at).toLocaleString()}</span>
              {t.message ? <div className='muted'>{t.message}</div> : null}
            </li>
          ))}
        </ul>
      </article>
    </Page>
  );
}

function Settings() {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Record<string, string>>({});
  const settingsTemplate = useMemo(
    () => ({
      ffmpeg_path: '',
      yt_dlp_path: '',
      openai_api_key: '',
      openai_base_url: 'https://api.openai.com/v1',
      lmstudio_base_url: 'http://localhost:1234/v1',
    }),
    [],
  );
  const settings = useQuery({ queryKey: ['settings'], queryFn: async () => (await api.get('/settings')).data as Record<string, string> });

  const save = useMutation({
    mutationFn: async (payload: Record<string, string>) => api.put('/settings', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings'] }),
  });

  const merged = { ...settingsTemplate, ...(settings.data ?? {}), ...draft };

  return (
    <Page title='Settings'>
      <article className='card'>
        <p className='muted'>
          If diagnostics shows <code>ffmpeg: false</code>, set <code>ffmpeg_path</code> to your executable path (for example,
          <code> C:\ffmpeg\bin\ffmpeg.exe</code>) and save.
        </p>
        <div className='stack'>
          {Object.entries(merged).map(([k, v]) => (
            <label key={k}>
              {k}
              <input value={v} onChange={(e) => setDraft((prev) => ({ ...prev, [k]: e.target.value }))} />
            </label>
          ))}
        </div>
        <button onClick={() => save.mutate(merged)} disabled={save.isPending}>Save settings</button>
      </article>
    </Page>
  );
}

function Diagnostics() {
  const diag = useQuery({ queryKey: ['diagnostics'], queryFn: async () => (await api.get('/diagnostics')).data });
  return (
    <Page title='Diagnostics'>
      <div className='grid'>
        {Object.entries(diag.data ?? {}).map(([k, v]) => (
          <article className='card stat' key={k}>
            <p className='label'>{k}</p>
            <p className='value'>{String(v)}</p>
          </article>
        ))}
      </div>
    </Page>
  );
}

function Logs() {
  const logs = useQuery({ queryKey: ['logs'], queryFn: async () => (await api.get('/logs')).data as Array<Record<string, any>> });
  return (
    <Page title='Logs'>
      <article className='card'>
        <ul className='stack'>
          {(logs.data ?? []).map((l) => (
            <li key={l.id}>
              <strong>[{l.severity}]</strong> <span className='muted'>{new Date(l.created_at).toLocaleString()}</span>
              <br />
              {l.context}: {l.message}
            </li>
          ))}
        </ul>
      </article>
    </Page>
  );
}

function Collections() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const collections = useQuery({ queryKey: ['collections'], queryFn: async () => (await api.get('/collections')).data as Collection[] });

  const create = useMutation({
    mutationFn: async () => api.post('/collections', { name }),
    onSuccess: () => {
      setName('');
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    },
  });

  return (
    <Page title='Collections'>
      <article className='card row'>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder='Collection name' />
        <button onClick={() => create.mutate()} disabled={!name.trim() || create.isPending}>Create collection</button>
      </article>

      <div className='grid'>
        {(collections.data ?? []).map((c) => (
          <article className='card stat' key={c.id}>
            <p className='label'>Collection</p>
            <p className='value'>{c.name}</p>
          </article>
        ))}
      </div>
    </Page>
  );
}

function Layout() {
  const links = [
    ['/', 'Home'],
    ['/sources', 'Sources'],
    ['/jobs', 'Jobs'],
    ['/library', 'Library'],
    ['/collections', 'Collections'],
    ['/settings', 'Settings'],
    ['/diagnostics', 'Diagnostics'],
    ['/logs', 'Logs'],
  ] as const;

  return (
    <div className='layout'>
      <aside>
        <h2>ReimagineDoomscrolling</h2>
        <nav>
          {links.map(([href, label]) => (
            <NavLink key={href} to={href} className={({ isActive }) => (isActive ? 'active' : '')} end={href === '/'}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main>
        <Routes>
          <Route path='/' element={<Home />} />
          <Route path='/sources' element={<Sources />} />
          <Route path='/jobs' element={<Jobs />} />
          <Route path='/library' element={<Library />} />
          <Route path='/collections' element={<Collections />} />
          <Route path='/reader/:id' element={<Reader />} />
          <Route path='/settings' element={<Settings />} />
          <Route path='/diagnostics' element={<Diagnostics />} />
          <Route path='/logs' element={<Logs />} />
        </Routes>
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
