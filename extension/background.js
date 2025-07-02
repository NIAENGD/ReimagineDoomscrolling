let running = false;
let ytTabId = null;
let gptTabId = null;
let options = { count: 6 };
let articles = [];
chrome.storage.local.get('articles', data => { articles = data.articles || []; });

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.cmd === 'start') {
    options = Object.assign(options, msg.opts || {});
    startProcessing();
  } else if (msg.cmd === 'stop') {
    running = false;
  } else if (msg.cmd === 'watchLike') {
    watchAndReact(msg.url, true);
  } else if (msg.cmd === 'watchDislike') {
    watchAndReact(msg.url, false);
  }
});

async function startProcessing() {
  if (running) return;
  running = true;
  ytTabId = await openTab('https://www.youtube.com');
  gptTabId = await openTab('https://chat.openai.com');
  chrome.runtime.sendMessage({status: 'gathering links...', progress: 0});
  const links = await collectLinks(ytTabId, options.count);
  chrome.runtime.sendMessage({status: 'processing ' + links.length + ' videos', progress: 0});
  let done = 0;
  for (const url of links) {
    if (!running) break;
    const transcript = await fetchTranscript(url);
    const result = await processTranscript(transcript);
    const title = await fetchTitle(url);
    articles.push({id: articles.length + 1, url, title, ...result});
    done++;
    chrome.runtime.sendMessage({progress: Math.round(done/links.length*100), status: `processed ${done}/${links.length}`});
  }
  chrome.storage.local.set({articles});
  chrome.runtime.sendMessage({status: 'done', progress: 100});
  running = false;
}

function openTab(url) {
  return new Promise(resolve => {
    chrome.tabs.create({url, active: false}, tab => resolve(tab.id));
  });
}

async function collectLinks(tabId, count) {
  let links = [];
  for (let i = 0; i < 20 && links.length < count; i++) {
    const res = await chrome.scripting.executeScript({
      target: {tabId},
      func: already => {
        window.scrollBy(0, window.innerHeight);
        const anchors = Array.from(document.querySelectorAll('a#thumbnail'));
        const hrefs = anchors.map(a => a.href)
          .filter(u => u.includes('watch') && !u.includes('shorts'));
        return hrefs.filter(u => !already.includes(u));
      },
      args: [links],
    });
    const newLinks = (res[0] && res[0].result) || [];
    for (const u of newLinks) if (!links.includes(u)) links.push(u);
    if (links.length < count) await new Promise(r => setTimeout(r, 1000));
  }
  return links.slice(0, count);
}

async function fetchTranscript(url) {
  const resp = await fetch('http://localhost:5001/api/subtitles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  const data = await resp.json();
  return data.transcript || '';
}

async function fetchTitle(url) {
  const id = await openTab(url);
  const res = await chrome.scripting.executeScript({
    target: { tabId: id },
    func: () => document.title
  });
  chrome.tabs.remove(id);
  return res[0]?.result || url;
}

async function processTranscript(transcript) {
  const scorePrompt = `SCORING_PROMPT\n\n${transcript}`;
  const scoreRes = await runChatPrompt(scorePrompt);
  let score = {};
  try { score = JSON.parse(scoreRes); } catch (e) {}
  const articleRes = await runChatPrompt(`REWRITE_PROMPT\n\n${transcript}`);
  return { score, article: articleRes, transcript };
}

async function runChatPrompt(prompt) {
  const res = await chrome.scripting.executeScript({
    target: { tabId: gptTabId },
    func: (p) => {
      const box = document.querySelector('textarea');
      if (!box) return '';
      box.value = p;
      box.dispatchEvent(new Event('input', { bubbles: true }));
      box.form.querySelector('button')?.click();
      return new Promise(resolve => {
        const obs = new MutationObserver(() => {
          const nodes = document.querySelectorAll('.markdown');
          const last = nodes[nodes.length - 1];
          if (last && last.textContent.trim()) {
            obs.disconnect();
            resolve(last.textContent);
          }
        });
        obs.observe(document.body, { childList: true, subtree: true });
      });
    },
    args: [prompt]
  });
  return res[0]?.result || '';
}

async function watchAndReact(url, like) {
  const id = await openTab(url);
  await chrome.scripting.executeScript({
    target: {tabId: id},
    func: (like) => {
      const vid = document.querySelector('video');
      if (vid) { vid.muted = true; vid.play(); }
      setTimeout(() => {
        if (like) {
          document.querySelector('ytd-toggle-button-renderer button')?.click();
        } else {
          document.querySelector('ytd-menu-renderer button')?.click();
          setTimeout(() => {
            const item = Array.from(document.querySelectorAll('ytd-menu-service-item-renderer')).find(el => el.textContent.toLowerCase().includes('not interested'));
            item?.click();
          }, 500);
        }
      }, 3000);
    },
    args: [like]
  });
  setTimeout(() => chrome.tabs.remove(id), 15000);
}
