const countEl = document.getElementById('count');
const scoreEl = document.getElementById('scorePrompt');
const rewriteEl = document.getElementById('rewritePrompt');
const progressEl = document.getElementById('progress');
const statusEl = document.getElementById('status');
const ytStatusEl = document.getElementById('ytStatus');
const gptStatusEl = document.getElementById('gptStatus');

document.getElementById('open').addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('results.html') });
});

const DEFAULT_SCORE_PROMPT = `You are an impartial video-analysis engine.\n\nINPUT\n———\n{{transcript}}\n\nTASK\n———\n(see rubric)`;
const DEFAULT_REWRITE_PROMPT = `以原作者视角，忠实呈现视频中的观点、思路、结构和情绪，不加任何旁人评价或个人观点。\n标题/小标题分明，段落清晰；语言优美自然，贴合原风格。\n原汁原味还原引用、比喻、故事、幽默等表现手法；保持视频作者的个性（如讽刺、深情等）。\n开头简要介绍视频内容，结尾收束主要结论或号召；绝不提及“视频”，直接以文章形式呈现。\n切记！这并不是一个TLDR，或是总结，而是完整的文稿。\n切记！这不是一个总结，你需要输出尽量还原原视频的长度。`;

async function checkLogin() {
  const yt = await chrome.cookies.getAll({ url: 'https://www.youtube.com' });
  const gpt = await chrome.cookies.getAll({ url: 'https://chat.openai.com' });
  ytStatusEl.textContent = 'YouTube: ' + (yt.length ? 'logged in' : 'NOT logged in');
  gptStatusEl.textContent = 'ChatGPT: ' + (gpt.length ? 'logged in' : 'NOT logged in');
  return yt.length > 0 && gpt.length > 0;
}

document.getElementById('start').addEventListener('click', async () => {
  if (!(await checkLogin())) {
    statusEl.textContent = 'Please log into YouTube and ChatGPT first';
    return;
  }
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
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.status) statusEl.textContent = msg.status;
  if (msg.progress != null) {
    progressEl.value = msg.progress;
  }
});

async function updateLogin() {
  await checkLogin();
}

updateLogin();
setInterval(updateLogin, 10000);

// Load saved options
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
