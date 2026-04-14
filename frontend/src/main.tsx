import React, { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import ReactDOM from 'react-dom/client';
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useNavigate,
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
import type { AxiosError } from 'axios';
import ReactMarkdown from 'react-markdown';
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

type Collection = { id: number; name: string };

type LibraryItem = {
  article_id: number;
  title: string;
  original_title?: string;
  version: number;
  body_preview: string;
  video_item_id: number;
  video_id?: string;
  video_url?: string;
  published_at?: string | null;
  source_title: string;
  source_id: number;
  thumbnail_url: string;
  transcript_source: string;
  video_category?: string;
  quality_score?: number;
  quality_report?: string;
  is_read: boolean;
  collections: Collection[];
  reading_progress: { position: number; total: number };
};

type Job = {
  id: number;
  type: string;
  status: string;
  created_at: string;
};

type ItemTransition = {
  id: number;
  to_status: string;
  message: string;
  created_at: string;
};

type LogEntry = {
  id: number;
  severity: string;
  context: string;
  message: string;
  created_at: string;
};

type SettingField = {
  key: string;
  label: string;
  type: 'text' | 'password' | 'url' | 'select' | 'range' | 'textarea';
  description?: string;
  options?: Array<{ label: string; value: string }>;
  min?: number;
  max?: number;
  step?: number;
};

type Notification = {
  id: number;
  kind: 'success' | 'error' | 'info';
  message: string;
};

const NotificationContext = React.createContext<{ notify: (message: string, kind?: Notification['kind']) => void }>({
  notify: () => undefined,
});

function useNotifications() {
  return React.useContext(NotificationContext);
}

function getApiErrorMessage(error: unknown, fallback: string) {
  const detail = (error as AxiosError<{ detail?: unknown }>)?.response?.data?.detail;
  if (typeof detail !== 'string') return fallback;
  const cleaned = detail.replace(/\\n/g, '\n').trim();
  return cleaned || fallback;
}

function Page({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className='page'>
      <div className='page-header'>
        <h1>{title}</h1>
        <p className='muted'>Control your reading pipeline with a cleaner, calmer workflow.</p>
      </div>
      {children}
    </section>
  );
}

function Home() {
  const sources = useQuery({ queryKey: ['sources'], queryFn: async () => (await api.get('/sources')).data as Source[] });
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: async () => (await api.get('/jobs')).data as Job[] });
  const library = useQuery({ queryKey: ['library-home'], queryFn: async () => (await api.get('/library')).data as LibraryItem[] });
  const scheduler = useQuery({ queryKey: ['scheduler'], queryFn: async () => (await api.get('/scheduler/status')).data });

  const activeSources = (sources.data ?? []).filter((s) => s.state === 'enabled').length;
  const unreadCount = (library.data ?? []).filter((a) => !a.is_read).length;
  const continueReading = (library.data ?? []).find((a) => (a.reading_progress.total || 0) > 0 && (a.reading_progress.position || 0) > 0 && !a.is_read);

  return (
    <Page title='Dashboard'>
      <article className='card hero'>
        <div>
          <p className='eyebrow'>Overview</p>
          <h2>Turn noisy video feeds into a focused reading queue.</h2>
          <p className='muted'>Track ingestion, quality, and progress without jumping between screens.</p>
        </div>
        <button onClick={() => { sources.refetch(); jobs.refetch(); library.refetch(); scheduler.refetch(); }}>Refresh dashboard</button>
      </article>
      <div className='grid'>
        <article className='card stat'><p className='label'>Sources</p><p className='value'>{sources.data?.length ?? 0}</p></article>
        <article className='card stat'><p className='label'>Active sources</p><p className='value'>{activeSources}</p></article>
        <article className='card stat'><p className='label'>Unread</p><p className='value'>{unreadCount}</p></article>
        <article className='card stat'><p className='label'>Scheduler</p><p className='value'>{String(scheduler.data?.enabled ?? false)}</p></article>
      </div>
      {continueReading ? (
        <article className='card'>
          <h2>Continue reading</h2>
          <p><Link to={`/reader/${continueReading.article_id}`}>{continueReading.title}</Link> · {continueReading.source_title}</p>
        </article>
      ) : null}
      <article className='card'>
        <h2>Latest articles</h2>
        <ul className='stack'>
          {(library.data ?? []).slice(0, 6).map((item) => (
            <li key={item.article_id}>
              <Link to={`/reader/${item.article_id}`}>{item.title}</Link>
              <div className='muted'>Channel: {item.source_title || 'Unknown source'}</div>
            </li>
          ))}
        </ul>
      </article>
      <article className='card'>
        <h2>Recent jobs</h2>
        <ul className='stack'>
          {(jobs.data ?? []).slice(0, 6).map((j) => <li key={j.id}>#{j.id} {j.type} · <span className='muted'>{j.status}</span></li>)}
        </ul>
      </article>
    </Page>
  );
}

function Sources() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { notify } = useNotifications();
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const sources = useQuery({ queryKey: ['sources'], queryFn: async () => (await api.get('/sources')).data as Source[] });
  const createSource = useMutation({
    mutationFn: async () => api.post('/sources', { title, url }),
    onSuccess: () => { setTitle(''); setUrl(''); queryClient.invalidateQueries({ queryKey: ['sources'] }); notify('Source added successfully.'); },
    onError: () => notify('Could not add source.', 'error'),
  });
  const updateSource = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Source> }) => api.patch(`/sources/${id}`, payload),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['sources'] }); notify('Source updated.'); },
    onError: () => notify('Source update failed.', 'error'),
  });
  const deleteSource = useMutation({
    mutationFn: async (id: number) => api.delete(`/sources/${id}`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['sources'] }); notify('Source removed.'); },
    onError: (error) => notify(getApiErrorMessage(error, 'Could not remove source.'), 'error'),
  });

  return (
    <Page title='Sources'>
      <article className='card'>
        <h2>Add source</h2>
        <form className='row' onSubmit={(e: FormEvent) => { e.preventDefault(); if (url.trim()) createSource.mutate(); }}>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder='Display title (optional)' />
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder='YouTube channel URL' required />
          <button>Add source</button>
        </form>
      </article>
      <div className='stack'>
        {(sources.data ?? []).map((src) => (
          <article className='card' key={src.id}>
            <h3><button className='linkish' onClick={() => navigate(`/sources/${src.id}`)}>{src.title || src.url}</button></h3>
            <p className='muted'>{src.url}</p>
            <div className='row'>
              <label>State <select value={src.state} onChange={(e) => updateSource.mutate({ id: src.id, payload: { state: e.target.value } })}><option value='enabled'>Enabled</option><option value='paused'>Paused</option><option value='archived'>Archived</option></select></label>
              <label>Cadence <input type='number' defaultValue={src.cadence_minutes} onBlur={(e) => updateSource.mutate({ id: src.id, payload: { cadence_minutes: Number(e.target.value) } })} /></label>
              <button
                type='button'
                onClick={() => {
                  if (window.confirm(`Remove "${src.title || src.url}" and all imported items?`)) {
                    deleteSource.mutate(src.id);
                  }
                }}
                disabled={deleteSource.isPending}
              >
                Remove source
              </button>
            </div>
          </article>
        ))}
      </div>
    </Page>
  );
}

function SourceDetail() {
  const { id } = useParams();
  const sourceId = Number(id);
  const source = useQuery({ queryKey: ['sources'], queryFn: async () => (await api.get('/sources')).data as Source[] });
  const { notify } = useNotifications();
  const logs = useQuery({
    queryKey: ['logs', sourceId],
    queryFn: async () => (await api.get('/logs', { params: { source_id: sourceId } })).data as LogEntry[],
    enabled: Number.isFinite(sourceId),
    refetchInterval: 5000,
  });
  const refresh = useMutation({
    mutationFn: async () => api.post(`/sources/${id}/refresh`),
    onSuccess: () => {
      source.refetch();
      logs.refetch();
      notify('Source refresh started.');
    },
    onError: () => notify('Source refresh failed.', 'error'),
  });
  const src = (source.data ?? []).find((s) => String(s.id) === id);
  const activeLogs = (logs.data ?? []).filter((entry) => entry.context.includes(`source_id=${sourceId}`));
  const latestLogs = activeLogs.slice(0, 10);

  return (
    <Page title='Source detail'>
      <article className='card stack'>
        <h2>{src?.title ?? 'Missing source'}</h2>
        <p>{src?.url}</p>
        <div className='row'>
          <button onClick={() => refresh.mutate()} disabled={refresh.isPending || !src}>
            {refresh.isPending ? 'Refreshing…' : 'Refresh now'}
          </button>
          <button onClick={() => logs.refetch()} disabled={logs.isFetching}>Reload activity</button>
        </div>
        <p className='muted'>
          {refresh.isPending ? 'Refresh is running. Activity updates every 5 seconds.' : 'Tip: keep this page open to watch refresh progress.'}
        </p>
      </article>
      <article className='card'>
        <h3>Latest activity</h3>
        <ul className='stack'>
          {latestLogs.length === 0 && <li className='muted'>No source-specific logs yet.</li>}
          {latestLogs.map((entry) => (
            <li key={entry.id}>
              <strong>[{entry.severity}]</strong> <span className='muted'>{new Date(entry.created_at).toLocaleString()}</span>
              <br />
              {entry.context}: {entry.message}
            </li>
          ))}
        </ul>
      </article>
    </Page>
  );
}

function Library() {
  const [params, setParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { notify } = useNotifications();
  const q = params.get('q') ?? '';
  const source = params.get('source') ?? '';
  const selectedChannel = params.get('channel') ?? 'all';
  const read_state = params.get('read_state') ?? '';
  const sort_by = params.get('sort_by') ?? 'import_time';
  const view = params.get('view') ?? 'grid';
  const collection_id = params.get('collection_id') ?? '';

  const collections = useQuery({ queryKey: ['collections'], queryFn: async () => (await api.get('/collections')).data as Collection[] });
  const library = useQuery({
    queryKey: ['library', q, source, read_state, sort_by, collection_id],
    queryFn: async () => (await api.get('/library', { params: { q, source, read_state, sort_by, collection_id: collection_id || undefined } })).data,
  });
  const entries = (library.data ?? []) as LibraryItem[];
  const channels = useMemo(
    () => ['all', ...Array.from(new Set(entries.map((item) => item.source_title).filter(Boolean))).sort((a, b) => a.localeCompare(b))],
    [entries],
  );
  const visibleEntries = selectedChannel === 'all' ? entries : entries.filter((item) => item.source_title === selectedChannel);

  const markRead = useMutation({
    mutationFn: async ({ articleId, isRead }: { articleId: number; isRead: boolean }) => api.post(`/articles/${articleId}/read-state`, { is_read: isRead }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['library'] }); notify('Read state updated.'); },
    onError: () => notify('Could not update read state.', 'error'),
  });
  const addToCollection = useMutation({
    mutationFn: async ({ articleId, collectionId }: { articleId: number; collectionId: number }) => api.post(`/collections/${collectionId}/articles/${articleId}`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['library'] }); notify('Added to collection.'); },
    onError: () => notify('Could not add to collection.', 'error'),
  });

  const set = (k: string, v: string) => { const next = Object.fromEntries(params.entries()); if (v) next[k] = v; else delete next[k]; setParams(next); };

  const thumbnailFor = (item: LibraryItem) => {
    if (item.thumbnail_url) return item.thumbnail_url;
    if (item.video_id) return `https://i.ytimg.com/vi/${item.video_id}/hqdefault.jpg`;
    const fromUrl = item.video_url?.split('v=')[1]?.split('&')[0];
    if (fromUrl) return `https://i.ytimg.com/vi/${fromUrl}/hqdefault.jpg`;
    return '';
  };

  const cards = (items: LibraryItem[]) => (
    <div className={view === 'list' ? 'stack library-cards list' : 'grid library-cards'}>
      {items.map((item) => (
        <article key={item.article_id} className='card'>
          {thumbnailFor(item) ? <img className='thumb' src={thumbnailFor(item)} alt={item.title} loading='lazy' /> : null}
          <h3>{item.title}</h3>
          <p className='muted'>
            {item.source_title} · v{item.version} · {item.published_at ? new Date(item.published_at).toLocaleDateString() : 'Unknown publish date'} · <span className='badge'>{item.transcript_source || 'unknown transcript'}</span>
          </p>
          {item.original_title && item.original_title !== item.title ? <p className='muted'><strong>Original:</strong> {item.original_title}</p> : null}
          <p className='row meta-row'>
            <span className='badge'>Category: {item.video_category || 'Unrated'}</span>
            <span className='badge'>Score: {item.quality_score ?? 0}</span>
          </p>
          <p>{item.body_preview || 'No preview available.'}</p>
          <div className='row'>
            <Link to={`/reader/${item.article_id}`}>Open reader</Link>
            <button onClick={() => markRead.mutate({ articleId: item.article_id, isRead: !item.is_read })}>{item.is_read ? 'Mark unread' : 'Mark read'}</button>
            <select defaultValue='' onChange={(e) => e.target.value && addToCollection.mutate({ articleId: item.article_id, collectionId: Number(e.target.value) })}>
              <option value=''>Add to collection</option>
              {(collections.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        </article>
      ))}
    </div>
  );

  return (
    <Page title='Library'>
      <section className='library-shell'>
        <aside className='card channel-filter'>
          <h3>Channels</h3>
          <p className='muted'>Filter by source</p>
          {channels.map((channel) => (
            <button
              key={channel}
              type='button'
              className={`chip ${selectedChannel === channel ? 'active' : ''}`}
              onClick={() => {
                set('channel', channel);
                set('source', channel === 'all' ? '' : channel);
              }}
            >
              <span>{channel === 'all' ? 'All channels' : channel}</span>
              <span className='muted'>{channel === 'all' ? entries.length : entries.filter((item) => item.source_title === channel).length}</span>
            </button>
          ))}
        </aside>
        <div className='library-content'>
          <article className='card library-toolbar'>
            <input placeholder='Search videos, channels, or article text' defaultValue={q} onChange={(e) => set('q', e.target.value)} />
            <select value={read_state} onChange={(e) => set('read_state', e.target.value)}><option value=''>All status</option><option value='unread'>Unread</option><option value='read'>Read</option></select>
            <select value={sort_by} onChange={(e) => set('sort_by', e.target.value)}><option value='import_time'>Newest imported</option><option value='publish_time'>Newest published</option><option value='source'>Channel A-Z</option><option value='title'>Title A-Z</option></select>
            <select value={collection_id} onChange={(e) => set('collection_id', e.target.value)}><option value=''>All collections</option>{(collections.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
            <select value={view} onChange={(e) => set('view', e.target.value)}><option value='grid'>Grid</option><option value='list'>List</option></select>
          </article>
          {cards(visibleEntries)}
        </div>
      </section>
    </Page>
  );
}

function Reader() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const articleRef = useRef<HTMLDivElement | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [tab, setTab] = useState<'article' | 'transcript'>('article');
  const [isWideReader, setIsWideReader] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const { notify } = useNotifications();

  const settings = useQuery({ queryKey: ['settings'], queryFn: async () => (await api.get('/settings')).data as Record<string, string> });
  const detail = useQuery({ queryKey: ['article', id], queryFn: async () => (await api.get(`/articles/${id}`)).data, enabled: Boolean(id) });
  const transcript = useQuery({ queryKey: ['transcript', detail.data?.video_item_id], queryFn: async () => (await api.get(`/transcripts/${detail.data?.video_item_id}`)).data, enabled: Boolean(detail.data?.video_item_id) });
  const timeline = useQuery({ queryKey: ['item-timeline', detail.data?.video_item_id], queryFn: async () => (await api.get(`/items/${detail.data?.video_item_id}/timeline`)).data as ItemTransition[], enabled: Boolean(detail.data?.video_item_id) });

  const regenerate = useMutation({
    mutationFn: async () => api.post(`/articles/${id}/regenerate`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['article', id] }); notify('Regeneration started.'); },
    onError: () => notify('Could not regenerate article.', 'error'),
  });
  const markRead = useMutation({
    mutationFn: async (isRead: boolean) => api.post(`/articles/${id}/read-state`, { is_read: isRead }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['article', id] }); notify('Read state updated.'); },
    onError: () => notify('Could not update read state.', 'error'),
  });
  const saveProgress = useMutation({ mutationFn: async (payload: { position: number; total: number }) => api.post(`/articles/${id}/progress`, payload) });

  const version = useMemo(() => {
    const versions = detail.data?.versions ?? [];
    if (!versions.length) return null;
    if (selectedVersion) return versions.find((v: any) => v.version === selectedVersion) ?? versions[0];
    return versions[0];
  }, [detail.data, selectedVersion]);

  const body = version?.body ?? '';
  const words = body.trim().split(/\s+/).filter(Boolean).length;
  const estMinutes = Math.max(1, Math.round(words / 220));
  const headings = body.split('\n').filter((l: string) => /^#{1,3}\s+/.test(l));

  useEffect(() => {
    const updateLayout = () => setIsWideReader(window.matchMedia('(min-width: 1360px) and (min-aspect-ratio: 4/3)').matches);
    updateLayout();
    window.addEventListener('resize', updateLayout);
    return () => window.removeEventListener('resize', updateLayout);
  }, []);

  const readerFont = settings.data?.reader_font_family || 'sans';
  const readerFontSize = Number(settings.data?.reader_font_size || 17);
  const readerWidth = Number(settings.data?.reader_line_width || 72);
  const activeContent = tab === 'article' ? (body || 'No content available.') : (transcript.data?.text || 'Transcript unavailable.');
  const pages = useMemo(() => {
    const paragraphs = activeContent.split(/\n{2,}/).filter(Boolean);
    if (!paragraphs.length) return ['No content available.'];
    const approxCharsPerLine = Math.max(42, Math.floor((isWideReader ? 108 : readerWidth) * 0.9));
    const approxLines = Math.max(12, Math.floor((window.innerHeight * 0.62) / Math.max(14, readerFontSize * 1.6)));
    const pageLimit = approxCharsPerLine * approxLines * (isWideReader ? 2 : 1);
    const paged: string[] = [];
    let current = '';
    paragraphs.forEach((paragraph) => {
      if ((current + paragraph).length > pageLimit && current.trim()) {
        paged.push(current.trim());
        current = paragraph;
      } else {
        current += `${current ? '\n\n' : ''}${paragraph}`;
      }
    });
    if (current.trim()) paged.push(current.trim());
    return paged.length ? paged : ['No content available.'];
  }, [activeContent, isWideReader, readerWidth, readerFontSize]);

  useEffect(() => {
    setCurrentPage(0);
  }, [tab, version?.version, detail.data?.id, isWideReader, readerWidth, readerFontSize]);

  useEffect(() => {
    if (!id || !pages.length) return;
    saveProgress.mutate({ position: currentPage + 1, total: pages.length });
  }, [currentPage, id, pages.length, saveProgress]);

  return (
    <Page title='Reader'>
      <article className='card'>
        <h2>{detail.data?.title ?? 'Loading...'}</h2>
        <p className='muted'>{detail.data?.source_title} · {detail.data?.source_url}</p>
        {detail.data?.original_title && detail.data?.original_title !== detail.data?.title ? (
          <p className='muted'><strong>Original YouTube title:</strong> {detail.data.original_title}</p>
        ) : null}
        <p className='row meta-row'>
          <span className='badge'>Category: {detail.data?.video_category || 'Unrated'}</span>
          <span className='badge'>Score: {detail.data?.quality_score ?? 0}</span>
        </p>
        {detail.data?.quality_report ? (
          <details>
            <summary>AI quality report</summary>
            <pre>{detail.data.quality_report}</pre>
          </details>
        ) : null}
        <div className='row'>
          <label>Version <select value={version?.version ?? ''} onChange={(e) => setSelectedVersion(Number(e.target.value))}>{(detail.data?.versions ?? []).map((v: any) => <option key={v.version} value={v.version}>v{v.version}</option>)}</select></label>
          <button onClick={() => regenerate.mutate()}>Regenerate</button>
          <button onClick={() => { detail.refetch(); transcript.refetch(); timeline.refetch(); }}>Refresh data</button>
          <button onClick={() => markRead.mutate(!detail.data?.is_read)}>{detail.data?.is_read ? 'Mark unread' : 'Mark read'}</button>
          <button onClick={() => navigator.clipboard.writeText(body).then(() => notify('Article copied to clipboard.')).catch(() => notify('Could not copy article.', 'error'))}>Copy</button>
          <span className='muted'>~{estMinutes} min read</span>
        </div>
        {!!headings.length && <details><summary>Headings</summary><ul>{headings.map((h, i) => <li key={i}>{h.replace(/^#{1,3}\s+/, '')}</li>)}</ul></details>}
      </article>

      <article className={`card reader reader-font-${readerFont} ${isWideReader ? 'reader-spread' : 'reader-single'}`} style={{ fontSize: `${readerFontSize}px`, maxWidth: isWideReader ? '100%' : `${readerWidth}ch` }}>
        <div className='tabs'><button className={tab === 'article' ? 'active' : ''} onClick={() => setTab('article')}>Article</button><button className={tab === 'transcript' ? 'active' : ''} onClick={() => setTab('transcript')}>Transcript</button></div>
        <div className='reader-pagination'>
          <button type='button' onClick={() => setCurrentPage((p) => Math.max(0, p - 1))} disabled={currentPage <= 0}>← Previous</button>
          <span className='muted'>Page {Math.min(currentPage + 1, pages.length)} of {pages.length}</span>
          <button type='button' onClick={() => setCurrentPage((p) => Math.min(pages.length - 1, p + 1))} disabled={currentPage >= pages.length - 1}>Next →</button>
        </div>
        <div ref={articleRef} className='reader-scroll'>
          <ReactMarkdown>{pages[currentPage] || ''}</ReactMarkdown>
        </div>
      </article>
      <article className='card'><h3>Processing timeline</h3><ul className='stack'>{(timeline.data ?? []).map((t) => <li key={t.id}><strong>{t.to_status}</strong> <span className='muted'>{new Date(t.created_at).toLocaleString()}</span>{t.message ? <div className='muted'>{t.message}</div> : null}</li>)}</ul></article>
    </Page>
  );
}

function CollectionsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { notify } = useNotifications();
  const [name, setName] = useState('');
  const collections = useQuery({ queryKey: ['collections'], queryFn: async () => (await api.get('/collections')).data as Collection[] });
  const detail = useQuery({ queryKey: ['collection', id], queryFn: async () => (await api.get(`/collections/${id}`)).data, enabled: Boolean(id) });

  const create = useMutation({
    mutationFn: async () => api.post('/collections', { name }),
    onSuccess: () => { setName(''); queryClient.invalidateQueries({ queryKey: ['collections'] }); notify('Collection created.'); },
    onError: () => notify('Could not create collection.', 'error'),
  });
  const rename = useMutation({
    mutationFn: async () => api.patch(`/collections/${id}`, { name }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['collection', id] }); notify('Collection renamed.'); },
    onError: () => notify('Could not rename collection.', 'error'),
  });
  const del = useMutation({
    mutationFn: async () => api.delete(`/collections/${id}`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['collections'] }); navigate('/collections'); notify('Collection deleted.'); },
    onError: () => notify('Could not delete collection.', 'error'),
  });
  const remove = useMutation({
    mutationFn: async (articleId: number) => api.delete(`/collections/${id}/articles/${articleId}`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['collection', id] }); notify('Article removed from collection.'); },
    onError: () => notify('Could not remove article.', 'error'),
  });

  return (
    <Page title='Collections'>
      <article className='card row'>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder='Collection name' />
        <button onClick={() => create.mutate()} disabled={!name.trim()}>Create collection</button>
      </article>
      <div className='grid'>
        {(collections.data ?? []).map((c) => <article className='card' key={c.id}><h3>{c.name}</h3><button onClick={() => navigate(`/collections/${c.id}`)}>Open</button></article>)}
      </div>
      {id && detail.data ? <article className='card'><h2>{detail.data.name}</h2><div className='row'><input value={name} onChange={(e) => setName(e.target.value)} placeholder='New name' /><button onClick={() => rename.mutate()}>Rename</button><button onClick={() => del.mutate()}>Delete</button></div><ul className='stack'>{(detail.data.articles ?? []).map((a: any) => <li key={a.article_id}>{a.title} <button onClick={() => remove.mutate(a.article_id)}>Remove</button></li>)}</ul></article> : null}
    </Page>
  );
}

function Settings() {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Record<string, string>>({});
  const { notify } = useNotifications();
  const settingsTemplate = useMemo(() => ({
    timezone: 'UTC',
    source_default_discovery_mode: 'latest_n', source_default_max_videos: '10', source_default_rolling_window_hours: '72', source_default_skip_shorts: 'true', source_default_min_duration_seconds: '180', source_default_dedup_policy: 'source_video_id',
    transcript_languages: 'en', transcript_first: 'true', transcript_fallback_enabled: 'true', whisper_model_size: 'base', transcription_cpu_threads: '4', transcription_language_hint: '',
    generation_provider: 'openai', generation_model: 'gpt-4.1-mini', generation_temperature: '0.2', generation_timeout_seconds: '300', generation_max_tokens: '30000', global_prompt_template: 'Convert the transcript into a polished article.\n\n{{transcript}}', openai_api_key: '', openai_base_url: 'https://api.openai.com/v1', lmstudio_base_url: 'http://localhost:1234/v1',
    title_prompt_template: 'Rewrite the video title into a descriptive, non-clickbait title that matches the transcript.',
    score_prompt_template: 'Evaluate this video transcript with strict scoring and concise rationale.',
    title_identifier_a: 'd}', title_identifier_b: '[/', title_identifier_c: '%x', title_identifier_d: '^#',
    reader_font_family: 'sans', reader_font_size: '17', reader_line_width: '72',
    scheduler_enabled: 'true', scheduler_default_cadence_minutes: '10', scheduler_concurrency_cap: '2',
  }), []);
  const settings = useQuery({ queryKey: ['settings'], queryFn: async () => (await api.get('/settings')).data as Record<string, string> });
  const save = useMutation({
    mutationFn: async (payload: Record<string, string>) => api.put('/settings', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setDraft({});
      notify('Settings saved.');
    },
    onError: () => notify('Settings failed to save.', 'error'),
  });

  const merged = { ...settingsTemplate, ...(settings.data ?? {}), ...draft };

  const groups: Array<{ title: string; description: string; fields: SettingField[] }> = [
    {
      title: 'General',
      description: 'Core app and interface defaults.',
      fields: [
        { key: 'timezone', label: 'Timezone', type: 'text', description: 'Used for schedules, logs, and timestamps.' },
      ],
    },
    {
      title: 'Source defaults',
      description: 'How new sources discover and filter content.',
      fields: [
        { key: 'source_default_discovery_mode', label: 'Discovery mode', type: 'select', options: [{ label: 'Latest N', value: 'latest_n' }, { label: 'Rolling window', value: 'rolling_window' }] },
        { key: 'source_default_max_videos', label: 'Max videos per run', type: 'range', min: 1, max: 100, step: 1 },
        { key: 'source_default_rolling_window_hours', label: 'Rolling window (hours)', type: 'range', min: 1, max: 336, step: 1 },
        { key: 'source_default_min_duration_seconds', label: 'Min duration (seconds)', type: 'range', min: 120, max: 600, step: 60, description: 'Range: 2 to 10 minutes.' },
        { key: 'source_default_skip_shorts', label: 'Skip shorts', type: 'select', options: [{ label: 'Enabled', value: 'true' }, { label: 'Disabled', value: 'false' }] },
        { key: 'source_default_dedup_policy', label: 'De-duplication', type: 'select', options: [{ label: 'Source video ID', value: 'source_video_id' }, { label: 'Title + source', value: 'title_source' }] },
      ],
    },
    {
      title: 'Transcript',
      description: 'Language strategy and transcription engine behavior.',
      fields: [
        { key: 'transcript_languages', label: 'Language priority', type: 'text', description: 'Comma-separated language codes, e.g. en,es.' },
        { key: 'transcript_first', label: 'Try transcript before ASR', type: 'select', options: [{ label: 'Enabled', value: 'true' }, { label: 'Disabled', value: 'false' }] },
        { key: 'transcript_fallback_enabled', label: 'Allow fallback', type: 'select', options: [{ label: 'Enabled', value: 'true' }, { label: 'Disabled', value: 'false' }] },
        { key: 'whisper_model_size', label: 'Whisper model', type: 'select', options: [{ label: 'Tiny', value: 'tiny' }, { label: 'Base', value: 'base' }, { label: 'Small', value: 'small' }, { label: 'Medium', value: 'medium' }, { label: 'Large', value: 'large' }] },
        { key: 'transcription_cpu_threads', label: 'CPU threads', type: 'range', min: 1, max: 32, step: 1 },
        { key: 'transcription_language_hint', label: 'Language hint', type: 'text' },
      ],
    },
    {
      title: 'Generation',
      description: 'Model provider and inference limits.',
      fields: [
        { key: 'generation_provider', label: 'Provider', type: 'select', options: [{ label: 'No AI (raw transcript)', value: 'raw' }, { label: 'OpenAI', value: 'openai' }, { label: 'LM Studio', value: 'lmstudio' }] },
        { key: 'generation_model', label: 'Model', type: 'text' },
        { key: 'global_prompt_template', label: 'Prompt template', type: 'textarea', description: 'Used for transcript-to-article generation. Supports {{transcript}} placeholder.' },
        { key: 'title_prompt_template', label: 'Title rewrite prompt', type: 'textarea', description: 'Dedicated prompt for clickbait-to-descriptive title rewriting.' },
        { key: 'score_prompt_template', label: 'Score prompt', type: 'textarea', description: 'Dedicated prompt for category + strict scoring output.' },
        { key: 'title_identifier_a', label: 'Title marker A', type: 'text' },
        { key: 'title_identifier_b', label: 'Title marker B', type: 'text' },
        { key: 'title_identifier_c', label: 'Title marker C', type: 'text' },
        { key: 'title_identifier_d', label: 'Title marker D', type: 'text' },
        { key: 'generation_temperature', label: 'Temperature', type: 'range', min: 0, max: 2, step: 0.1 },
        { key: 'generation_timeout_seconds', label: 'Timeout (seconds)', type: 'range', min: 300, max: 3600, step: 30 },
        { key: 'generation_max_tokens', label: 'Max tokens', type: 'range', min: 100, max: 30000, step: 100 },
        { key: 'openai_base_url', label: 'OpenAI base URL', type: 'url' },
        { key: 'openai_api_key', label: 'OpenAI API key', type: 'password' },
        { key: 'lmstudio_base_url', label: 'LM Studio base URL', type: 'url' },
      ],
    },
    {
      title: 'Reader',
      description: 'Reading experience defaults for typography and layout.',
      fields: [
        { key: 'reader_font_family', label: 'Font family', type: 'select', options: [{ label: 'Sans', value: 'sans' }, { label: 'Serif', value: 'serif' }] },
        { key: 'reader_font_size', label: 'Font size', type: 'range', min: 12, max: 30, step: 1 },
        { key: 'reader_line_width', label: 'Line width (ch)', type: 'range', min: 45, max: 110, step: 1 },
      ],
    },
    {
      title: 'Scheduler',
      description: 'Background job cadence and concurrency.',
      fields: [
        { key: 'scheduler_enabled', label: 'Scheduler enabled', type: 'select', options: [{ label: 'Enabled', value: 'true' }, { label: 'Disabled', value: 'false' }] },
        { key: 'scheduler_default_cadence_minutes', label: 'Default cadence (minutes)', type: 'range', min: 1, max: 1440, step: 1 },
        { key: 'scheduler_concurrency_cap', label: 'Concurrency cap', type: 'range', min: 1, max: 32, step: 1 },
      ],
    },
  ];

  const onFieldChange = (key: string, value: string) => setDraft((p) => ({ ...p, [key]: value }));

  return (
    <Page title='Settings'>
      <article className='card settings-toolbar'>
        <div>
          <h2>System settings</h2>
          <p className='muted'>Control panel layout with grouped sections, field labels, and saved-value previews.</p>
        </div>
        <button onClick={() => {
          const changes = Object.fromEntries(
            Object.entries(draft).filter(([_, value]) => value !== '***redacted***'),
          );
          if (!Object.keys(changes).length) {
            notify('No settings changes to save.', 'info');
            return;
          }
          save.mutate(changes);
        }}
        >Save settings</button>
      </article>
      <article className='card settings-section-index'>
        <p className='muted'>Sections</p>
        <div className='row'>
          {groups.map((group) => <a key={group.title} href={`#settings-${group.title.replaceAll(' ', '-').toLowerCase()}`}>{group.title}</a>)}
        </div>
      </article>
      <div className='settings-grid settings-grid-wide'>
        {groups.map((group) => (
          <article className='card settings-group' key={group.title} id={`settings-${group.title.replaceAll(' ', '-').toLowerCase()}`}>
            <header>
              <h3>{group.title}</h3>
              <p className='muted'>{group.description}</p>
            </header>
            <div className='stack'>
              {group.fields.map((field) => {
                const value = merged[field.key] ?? '';
                return (
                  <label className='settings-field' key={field.key}>
                    <div className='space-between'>
                      <span>{field.label}</span>
                      <code>{value || '—'}</code>
                    </div>
                    {field.type === 'select' ? (
                      <select value={value} onChange={(e) => onFieldChange(field.key, e.target.value)}>
                        {(field.options ?? []).map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                      </select>
                    ) : field.type === 'range' ? (
                      <input
                        type='range'
                        value={value}
                        min={field.min}
                        max={field.max}
                        step={field.step}
                        onChange={(e) => onFieldChange(field.key, e.target.value)}
                      />
                    ) : field.type === 'textarea' ? (
                      <textarea
                        value={value}
                        onChange={(e) => onFieldChange(field.key, e.target.value)}
                        rows={6}
                      />
                    ) : (
                      <input
                        type={field.type}
                        value={value}
                        onChange={(e) => onFieldChange(field.key, e.target.value)}
                        autoComplete='off'
                      />
                    )}
                    {field.description ? <small className='muted'>{field.description}</small> : null}
                  </label>
                );
              })}
            </div>
          </article>
        ))}
      </div>
    </Page>
  );
}

function Diagnostics() {
  const diag = useQuery({ queryKey: ['diagnostics'], queryFn: async () => (await api.get('/diagnostics')).data });
  const renderValue = (value: unknown) => {
    if (value === null || value === undefined) return <span className='muted'>Unavailable</span>;
    if (typeof value === 'object') {
      const entries = Object.entries(value as Record<string, unknown>);
      if (!entries.length) return <span className='muted'>No details</span>;
      return (
        <dl className='diag-list'>
          {entries.map(([k, v]) => (
            <React.Fragment key={k}>
              <dt>{k}</dt>
              <dd>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</dd>
            </React.Fragment>
          ))}
        </dl>
      );
    }
    return <span>{String(value)}</span>;
  };

  return (
    <Page title='Diagnostics'>
      <article className='card'>
        <h2>Component health</h2>
        <p className='muted'>Live status and detailed values for backend dependencies.</p>
      </article>
      <div className='settings-grid'>
        {Object.entries(diag.data ?? {}).map(([k, v]) => (
          <article className='card diag-card' key={k}>
            <p className='label'>{k.replaceAll('_', ' ')}</p>
            {renderValue(v)}
          </article>
        ))}
      </div>
    </Page>
  );
}

function Logs() {
  const logs = useQuery({ queryKey: ['logs'], queryFn: async () => (await api.get('/logs')).data as Array<Record<string, any>> });
  return <Page title='Logs'><article className='card'><ul className='stack'>{(logs.data ?? []).map((l) => <li key={l.id}><strong>[{l.severity}]</strong> <span className='muted'>{new Date(l.created_at).toLocaleString()}</span><br />{l.context}: {l.message}</li>)}</ul></article></Page>;
}

function Layout() {
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const notify = (message: string, kind: Notification['kind'] = 'success') => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setNotifications((prev) => [...prev, { id, message, kind }]);
    window.setTimeout(() => setNotifications((prev) => prev.filter((item) => item.id !== id)), 3500);
  };
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  const links = [
    ['/', 'Home', '🏠'],
    ['/sources', 'Sources', '📺'],
    ['/jobs', 'Jobs', '🛠️'],
    ['/library', 'Library', '📚'],
    ['/collections', 'Collections', '🗂️'],
    ['/settings', 'Settings', '⚙️'],
    ['/diagnostics', 'Diagnostics', '🩺'],
    ['/logs', 'Logs', '📜'],
  ] as const;
  return (
    <NotificationContext.Provider value={{ notify }}>
      <div className={`layout ${navCollapsed ? 'nav-collapsed' : ''}`}>
        <aside>
        <div className='sidebar-shell'>
          <div className='sidebar-top'>
            {!navCollapsed ? <><h2>ReimagineDoomscrolling</h2><p className='muted product-subtitle'>Reader OS</p></> : null}
            <button type='button' className='nav-toggle' onClick={() => setNavCollapsed((v) => !v)}>{navCollapsed ? '⮞' : '⮜'}</button>
          </div>
          <nav>
            {links.map(([href, label, icon]) => (
              <NavLink key={href} to={href} className={({ isActive }) => (isActive ? 'active' : '')} end={href === '/'}>
                <span className='nav-icon'>{icon}</span>
                {!navCollapsed ? <span>{label}</span> : null}
              </NavLink>
            ))}
          </nav>
          {!navCollapsed ? <div className='sidebar-footer muted'>Monochrome UI locked</div> : null}
        </div>
        </aside>
        <main>
          <Routes>
            <Route path='/' element={<Home />} />
            <Route path='/sources' element={<Sources />} />
            <Route path='/sources/:id' element={<SourceDetail />} />
            <Route path='/jobs' element={<Jobs />} />
            <Route path='/library' element={<Library />} />
            <Route path='/collections' element={<CollectionsPage />} />
            <Route path='/collections/:id' element={<CollectionsPage />} />
            <Route path='/reader/:id' element={<Reader />} />
            <Route path='/settings' element={<Settings />} />
            <Route path='/diagnostics' element={<Diagnostics />} />
            <Route path='/logs' element={<Logs />} />
          </Routes>
        </main>
      </div>
      <div className='notification-stack' aria-live='polite'>
        {notifications.map((item) => (
          <div key={item.id} className={`notification ${item.kind}`}>
            <span>{item.message}</span>
            <button type='button' onClick={() => setNotifications((prev) => prev.filter((n) => n.id !== item.id))}>Dismiss</button>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
}

function Jobs() {
  const queryClient = useQueryClient();
  const { notify } = useNotifications();
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: async () => (await api.get('/jobs')).data as Job[] });
  const retry = useMutation({
    mutationFn: async (id: number) => api.post(`/jobs/${id}/retry`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['jobs'] }); notify('Job retry queued.'); },
    onError: () => notify('Job retry failed.', 'error'),
  });
  return (
    <Page title='Jobs'>
      <article className='card'><table><thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Created</th><th>Action</th></tr></thead><tbody>{(jobs.data ?? []).map((job) => <tr key={job.id}><td>{job.id}</td><td>{job.type}</td><td>{job.status}</td><td>{new Date(job.created_at).toLocaleString()}</td><td>{job.status.includes('fail') ? <button onClick={() => retry.mutate(job.id)}>Retry</button> : <span className='muted'>—</span>}</td></tr>)}</tbody></table></article>
    </Page>
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
