const countEl = document.getElementById('count');
const scoreEl = document.getElementById('scorePrompt');
const rewriteEl = document.getElementById('rewritePrompt');
const progressEl = document.getElementById('progress');
const statusEl = document.getElementById('status');
const logEl = document.getElementById('log');
const ytStatusEl = document.getElementById('ytStatus');
const gptStatusEl = document.getElementById('gptStatus');

function addLog(text) {
  const div = document.createElement('div');
  div.textContent = text;
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
}

document.getElementById('open').addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('results.html') });
});

const DEFAULT_SCORE_PROMPT = `You are an impartial video-analysis engine.

INPUT
———
{{transcript}}

TASK
———
1. **Pre-processing**
   • Remove or ignore all segments that are clearly promotional, sponsored, or ad-read in nature.
   • Evaluate only the substantive, non-advertisement content.

2. **Scoring (0-100, decimals allowed)**
   Apply the *strict* rubric below to each dimension.
   • A typical, average-quality video transcript scores **< 30**.
   • Only truly exceptional work reaches **> 60**.
   • Nobody scores 100.
   • Score each dimension independently; do **not** calculate or output any totals.

   | Dimension (JSON key) | 0 – 19 (Poor) | 20 – 39 (Weak) | 40 – 59 (Fair) | 60 – 79 (Strong) | 80 – 100 (Exceptional) |
   |----------------------|---------------|----------------|----------------|------------------|------------------------|
   | **logic**            | Incoherent, contradictory, or overtly misleading | Frequent gaps or fallacies | Generally coherent but with some leaps or ambiguities | Clear, sequential, few minor issues | Crystal-clear, airtight, zero misleading cues |
   | **depth**            | Surface-level, anecdotal | Minimal background/context | Moderately deep; some causal links | Thorough causal & systemic analysis | Multi-layer, root-cause & systemic depth |
   | **insight**          | Trivial or common knowledge | Few minor takeaways | Some new angles, limited originality | Several fresh, actionable insights | Breakthrough, paradigm-shifting insights |
   | **expression**       | Robotic or disjointed | Stiff, monotonous | Mostly natural; occasional dull moments | Engaging, vivid narration | Highly vivid, memorable storytelling |
   | **inspiration**      | None; flat | Slightly motivating | Moderately inspiring | Strongly motivating | Profoundly energising & empowering |
   | **overallQuality**   | Holistically synthesize the above (but do **not** average them mechanically); apply the same 0-100 scale |

3. **Blind-Spots & Challenges**
   Craft **one concise sentence** (≤ 35 words) flagging any major bias, commercial tilt, feasibility gaps, risk omissions, or likely misinterpretations the audience might overlook. Be specific, rational, and avoid clichés.

OUTPUT
———
Return **only** the following JSON (no commentary):

{
  "logic": <float>,
  "depth": <float>,
  "insight": <float>,
  "expression": <float>,
  "inspiration": <float>,
  "overallQuality": <float>,
  "blindSpots": "<single sentence here>"
}`;
const DEFAULT_REWRITE_PROMPT = `以原作者视角，忠实呈现视频中的观点、思路、结构和情绪，不加任何旁人评价或个人观点。\n标题/小标题分明，段落清晰；语言优美自然，贴合原风格。\n原汁原味还原引用、比喻、故事、幽默等表现手法；保持视频作者的个性（如讽刺、深情等）。\n开头简要介绍视频内容，结尾收束主要结论或号召；绝不提及“视频”，直接以文章形式呈现。\n切记！这并不是一个TLDR，或是总结，而是完整的文稿。\n切记！这不是一个总结，你需要输出尽量还原原视频的长度。`;

async function checkLogin() {
  const yt = await chrome.cookies.getAll({ url: 'https://www.youtube.com' });
  const gpt = await chrome.cookies.getAll({ url: 'https://chat.openai.com' });
  const gptAlt = await chrome.cookies.getAll({ url: 'https://chatgpt.com' });
  ytStatusEl.textContent = yt.length ? 'YouTube: logged in' : '';
  gptStatusEl.textContent = (gpt.length || gptAlt.length) ? 'ChatGPT: logged in' : '';
  return yt.length > 0 && (gpt.length > 0 || gptAlt.length > 0);
}

document.getElementById('openTabs').addEventListener('click', () => {
  chrome.runtime.sendMessage({ cmd: 'openTabs' });
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
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.log) addLog(msg.log);
  if (msg.status) addLog(msg.status);
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
