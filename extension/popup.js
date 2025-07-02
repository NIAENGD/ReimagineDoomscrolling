const countEl = document.getElementById('count');
const modelEl = document.getElementById('model');
const progressEl = document.getElementById('progress');
const statusEl = document.getElementById('status');
const ytStatusEl = document.getElementById('ytStatus');
const gptStatusEl = document.getElementById('gptStatus');

document.getElementById('open').addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:5001' });
});

document.getElementById('start').addEventListener('click', async () => {
  const opts = { count: Number(countEl.value), model: modelEl.value };
  await chrome.storage.local.set({ opts });
  chrome.runtime.sendMessage({ cmd: 'start', opts });
});

document.getElementById('stop').addEventListener('click', () => {
  chrome.runtime.sendMessage({ cmd: 'stop' });
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.status) statusEl.textContent = msg.status;
  if (msg.progress != null) {
    progressEl.value = msg.progress;
  }
});

async function updateLogin() {
  const yt = await chrome.cookies.getAll({url: 'https://www.youtube.com'});
  ytStatusEl.textContent = 'YouTube: ' + (yt.length ? 'logged in' : 'NOT logged in');
  const gpt = await chrome.cookies.getAll({url: 'https://chat.openai.com'});
  gptStatusEl.textContent = 'ChatGPT: ' + (gpt.length ? 'logged in' : 'NOT logged in');
}

updateLogin();

// Load saved options
chrome.storage.local.get('opts', (data) => {
  if (data.opts) {
    countEl.value = data.opts.count || 6;
    modelEl.value = data.opts.model || 'gpt-3.5-turbo';
  }
});
