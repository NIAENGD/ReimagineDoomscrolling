const countEl = document.getElementById('count');
const scoreEl = document.getElementById('scorePrompt');
const rewriteEl = document.getElementById('rewritePrompt');
const progressEl = document.getElementById('progress');
const statusEl = document.getElementById('status');
const logEl = document.getElementById('log');
const ytStatusEl = document.getElementById('ytStatus');
const gptStatusEl = document.getElementById('gptStatus');
const serverStatusEl = document.getElementById('serverStatus');

function addLog(text) {
  const div = document.createElement('div');
  div.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
}

document.getElementById('open').addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('results.html') });
});

const DEFAULT_SCORE_PROMPT = `You are an impartial video-analysis engine.\n\nINPUT\n———\n{{transcript}}\n\nTASK\n———\n1. Remove promotional segments before evaluating.\n2. Score logic, depth, insight, expression, inspiration, overallQuality on a strict 0-100 scale.\n3. Return one concise blind-spots sentence.\n\nOUTPUT\n———\nReturn only JSON:\n{\n  "logic": <float>,\n  "depth": <float>,\n  "insight": <float>,\n  "expression": <float>,\n  "inspiration": <float>,\n  "overallQuality": <float>,\n  "blindSpots": "<single sentence>"\n}`;

const DEFAULT_REWRITE_PROMPT = `以原作者视角，忠实呈现视频中的观点、思路、结构和情绪，不加旁人评价。\n标题和小标题分明，段落清晰。\n保持原文风格与叙事语气，不要写成摘要。\n输出尽量接近原视频信息量的完整文章。`;

async function checkLogin() {
  const yt = await chrome.cookies.getAll({ url: 'https://www.youtube.com' });
  const gpt = await chrome.cookies.getAll({ url: 'https://chat.openai.com' });
  const gptAlt = await chrome.cookies.getAll({ url: 'https://chatgpt.com' });

  ytStatusEl.textContent = yt.length ? 'YouTube ✓' : 'YouTube not logged in';
  gptStatusEl.textContent = (gpt.length || gptAlt.length) ? 'ChatGPT ✓' : 'ChatGPT not logged in';
}

async function checkServer() {
  try {
    const res = await fetch('http://localhost:5001/api/health');
    if (!res.ok) throw new Error('not ok');
    serverStatusEl.textContent = 'Online';
    serverStatusEl.classList.add('ok');
  } catch (e) {
    serverStatusEl.textContent = 'Offline';
    serverStatusEl.classList.remove('ok');
  }
}

document.getElementById('openTabs').addEventListener('click', () => {
  chrome.runtime.sendMessage({ cmd: 'openTabs' });
  addLog('Opening YouTube + ChatGPT windows…');
});

document.getElementById('start').addEventListener('click', async () => {
  const opts = {
    count: Number(countEl.value),
    scorePrompt: scoreEl.value || DEFAULT_SCORE_PROMPT,
    rewritePrompt: rewriteEl.value || DEFAULT_REWRITE_PROMPT
  };
  await chrome.storage.local.set({ opts });
  chrome.runtime.sendMessage({ cmd: 'start', opts });
});

document.getElementById('stop').addEventListener('click', () => {
  chrome.runtime.sendMessage({ cmd: 'stop' });
  addLog('Requested stop.');
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.log) addLog(msg.log);
  if (msg.status) statusEl.textContent = msg.status;
  if (msg.progress != null) progressEl.value = msg.progress;
});

async function refreshStatus() {
  await Promise.all([checkLogin(), checkServer()]);
}

refreshStatus();
setInterval(refreshStatus, 8000);

chrome.storage.local.get('opts', (data) => {
  if (data.opts) {
    countEl.value = data.opts.count || 6;
    scoreEl.value = data.opts.scorePrompt || DEFAULT_SCORE_PROMPT;
    rewriteEl.value = data.opts.rewritePrompt || DEFAULT_REWRITE_PROMPT;
  } else {
    scoreEl.value = DEFAULT_SCORE_PROMPT;
    rewriteEl.value = DEFAULT_REWRITE_PROMPT;
  }
});
