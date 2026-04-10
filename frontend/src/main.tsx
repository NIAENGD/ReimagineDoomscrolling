import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { api } from './lib/api';

const qc = new QueryClient();

function Home() { const {data} = useQuery({queryKey:['lib'], queryFn: async()=> (await api.get('/library')).data}); return <div><h1>Home</h1><p>Latest articles: {data?.length ?? 0}</p></div> }
function Sources() { const {data, refetch}=useQuery({queryKey:['sources'], queryFn: async()=> (await api.get('/sources')).data}); return <div><h1>Sources</h1><button onClick={async()=>{await api.post('/sources',{url:'https://youtube.com/channel/demo',title:'Demo'}); refetch();}}>Add Demo</button><ul>{data?.map((s:any)=><li key={s.id}>{s.title}</li>)}</ul></div>; }
function Jobs(){ const {data}=useQuery({queryKey:['jobs'], queryFn: async()=> (await api.get('/jobs')).data}); return <div><h1>Jobs</h1><pre>{JSON.stringify(data,null,2)}</pre></div>}
function Library(){ const {data}=useQuery({queryKey:['library'], queryFn: async()=> (await api.get('/library')).data}); return <div><h1>Library</h1><ul>{data?.map((a:any)=><li key={a.article_id}><Link to={`/reader/${a.article_id}`}>{a.title}</Link></li>)}</ul></div>}
function Reader(){return <div><h1>Reader</h1><p>Use article route id to read.</p></div>}
function Settings(){return <div><h1>Settings</h1></div>}
function Diagnostics(){const {data}=useQuery({queryKey:['diag'], queryFn: async()=> (await api.get('/diagnostics')).data}); return <div><h1>Diagnostics</h1><pre>{JSON.stringify(data,null,2)}</pre></div>}
function Logs(){const {data}=useQuery({queryKey:['logs'], queryFn: async()=> (await api.get('/logs')).data}); return <div><h1>Logs</h1><pre>{JSON.stringify(data,null,2)}</pre></div>}
function Collections(){return <div><h1>Collections</h1></div>}

function App(){return <div><nav style={{display:'flex',gap:12}}>{['/','/sources','/jobs','/library','/collections','/settings','/diagnostics','/logs'].map(p=><Link key={p} to={p}>{p}</Link>)}</nav><Routes><Route path='/' element={<Home/>}/><Route path='/sources' element={<Sources/>}/><Route path='/jobs' element={<Jobs/>}/><Route path='/library' element={<Library/>}/><Route path='/collections' element={<Collections/>}/><Route path='/reader/:id' element={<Reader/>}/><Route path='/settings' element={<Settings/>}/><Route path='/diagnostics' element={<Diagnostics/>}/><Route path='/logs' element={<Logs/>}/></Routes></div>}

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={qc}><BrowserRouter><App/></BrowserRouter></QueryClientProvider></React.StrictMode>);
