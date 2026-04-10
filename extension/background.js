let running = false;
let ytTabId = null;
let gptTabId = null;
let ytWindowId = null;
let gptWindowId = null;
let options = { count: 6, scorePrompt: '', rewritePrompt: '' };
let articles = [];

chrome.storage.local.get('articles', (data) => {
  articles = data.articles || [];
});

function log(msg) {
  chrome.runtime.sendMessage({ log: msg });
}

function setStatus(status, progress) {
  chrome.runtime.sendMessage({ status, progress });
}

async function persistArticle(a) {
  try {
    const resp = await fetch('http://localhost:5001/api/article', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(a)
    });
    const data = await resp.json();
    if (data.id) a.id = data.id;
  } catch (e) {
    console.error('persistArticle', e);
  }
}

chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({ url: chrome.runtime.getURL('popup.html') });
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.cmd === 'start') {
    options = Object.assign(options, msg.opts || {});
    startProcessing();
  } else if (msg.cmd === 'openTabs') {
    openTabs();
  } else if (msg.cmd === 'stop') {
    running = false;
    cleanupTabs();
    setStatus('Stopped', 0);
  } else if (msg.cmd === 'watchLike') {
    watchAndReact(msg.url, true);
  } else if (msg.cmd === 'watchDislike') {
    watchAndReact(msg.url, false);
  }
});

chrome.commands.onCommand.addListener((command) => {
  if (command === 'stop-processing') {
    running = false;
    cleanupTabs();
    setStatus('Stopped by keyboard shortcut', 0);
  }
});

function parseJsonObject(text) {
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch (_) {
    const match = text.match(/\{[\s\S]*\}/);
    if (!match) return {};
    try {
      return JSON.parse(match[0]);
    } catch {
      return {};
    }
  }
}

async function startProcessing() {
  if (running) return;
  running = true;

  if (!ytTabId || !gptTabId) {
    await openTabs();
  }

  log('Gathering links from YouTube home feed...');
  setStatus('Gathering links...', 3);

  const links = await collectLinks(ytTabId, options.count);
  const deduped = links.filter((url) => !articles.some((a) => a.url === url));

  if (!deduped.length) {
    setStatus('No new videos found (all already processed).', 100);
    running = false;
    return;
  }

  log(`Processing ${deduped.length} videos...`);

  let done = 0;
  for (const url of deduped) {
    if (!running) break;
    try {
      const transcriptData = await fetchTranscript(url);
      const title = transcriptData.title || await fetchTitle(url);
      const transcript = transcriptData.transcript || '';

      if (!transcript.trim()) {
        throw new Error('No transcript/subtitle available');
      }

      const result = await processTranscript(transcript, title);
      const article = { id: articles.length + 1, url, title, ...result };
      await persistArticle(article);
      articles.push(article);
      log(`✓ ${title} (${transcriptData.source || 'unknown source'})`);
    } catch (e) {
      console.error('Error processing video', url, e);
      log(`✗ ${url} :: ${e.message}`);
    }

    done++;
    setStatus(`Processed ${done}/${deduped.length}`, Math.round((done / deduped.length) * 100));
  }

  chrome.storage.local.set({ articles });
  setStatus('Done', 100);
  log('Run finished.');
  running = false;
  cleanupTabs();
}

function openPopup(url, opts = {}) {
  return new Promise((resolve) => {
    if (opts.windowId) {
      chrome.tabs.create({ url, active: false, windowId: opts.windowId }, (tab) => {
        resolve({ windowId: opts.windowId, tabId: tab.id, createdWindow: false });
      });
    } else {
      chrome.windows.create(
        {
          url,
          type: 'popup',
          focused: true,
          state: 'normal',
          left: opts.left,
          top: opts.top,
          width: opts.width,
          height: opts.height
        },
        (win) => {
          resolve({ windowId: win.id, tabId: win.tabs[0].id, createdWindow: true });
        }
      );
    }
  });
}

function waitTabComplete(tabId) {
  return new Promise((resolve) => {
    const listener = (id, info) => {
      if (id === tabId && info.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
  });
}

async function ensureChatGPTReady() {
  for (let i = 0; i < 50; i++) {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: gptTabId },
      func: () => Boolean(window.waitAssistantReply)
    });
    if (result) return true;
    await new Promise((r) => setTimeout(r, 400));
  }
  return false;
}

async function openTabs() {
  cleanupTabs();

  const displays = await chrome.system.display.getInfo();
  const { workArea } = displays[0];
  const halfWidth = Math.floor(workArea.width / 2);

  const yt = await openPopup('https://www.youtube.com', {
    left: workArea.left,
    top: workArea.top,
    width: halfWidth,
    height: workArea.height
  });
  ytWindowId = yt.windowId;
  ytTabId = yt.tabId;
  await waitTabComplete(ytTabId);

  const gpt = await openPopup('https://chatgpt.com', {
    left: workArea.left + halfWidth,
    top: workArea.top,
    width: workArea.width - halfWidth,
    height: workArea.height
  });
  gptWindowId = gpt.windowId;
  gptTabId = gpt.tabId;
  await waitTabComplete(gptTabId);
  await ensureChatGPTReady();

  fetch('http://localhost:5001/api/arrange', { method: 'POST' }).catch(() => {});
  log('YouTube and ChatGPT tabs opened side-by-side.');
}

async function collectLinks(tabId, count) {
  async function gather(seen = []) {
    const res = await chrome.scripting.executeScript({
      target: { tabId },
      func: (alreadySeen) => {
        const urls = [];
        const cards = document.querySelectorAll('ytd-rich-item-renderer');
        for (const card of cards) {
          if (card.querySelector('ytd-display-ad-renderer')) continue;
          if (card.innerText.includes('Sponsored')) continue;

          const link = card.querySelector('a#thumbnail[href], a#video-title-link[href]');
          if (!link) continue;

          const href = link.getAttribute('href') || '';
          if (href.startsWith('/shorts/')) continue;

          const url = new URL(href, 'https://www.youtube.com').href;
          if (!alreadySeen.includes(url)) urls.push(url);
        }
        return urls;
      },
      args: [seen]
    });
    return (res[0] && res[0].result) || [];
  }

  let links = [];
  let stagnantRounds = 0;

  for (let round = 0; round < 12 && links.length < count && stagnantRounds < 3; round++) {
    const more = await gather(links);
    const before = links.length;

    for (const u of more) {
      if (!links.includes(u)) links.push(u);
    }

    if (links.length === before) stagnantRounds++;
    else stagnantRounds = 0;

    await chrome.scripting.executeScript({
      target: { tabId },
      func: () => window.scrollBy(0, Math.max(window.innerHeight * 0.9, 600))
    });

    await new Promise((r) => setTimeout(r, 1200));
  }

  return links.slice(0, count);
}

async function fetchTranscript(url) {
  const resp = await fetch('http://localhost:5001/api/subtitles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });

  if (!resp.ok) throw new Error('Transcript server request failed');
  return resp.json();
}

async function fetchTitle(url) {
  const popup = await openPopup(url, ytWindowId ? { windowId: ytWindowId } : {});
  await waitTabComplete(popup.tabId);
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: popup.tabId },
      func: () => document.title || ''
    });
    return result || url;
  } finally {
    if (popup.createdWindow) chrome.windows.remove(popup.windowId);
    else chrome.tabs.remove(popup.tabId);
  }
}

async function processTranscript(transcript, title) {
  log(`Scoring: ${title}`);
  const scoreRes = await runChatPrompt(`${options.scorePrompt}\n\n${transcript}`);
  const score = parseJsonObject(scoreRes);

  log(`Rewriting: ${title}`);
  const articleRes = await runChatPrompt(`${options.rewritePrompt}\n\n${transcript}`);

  return { score, article: articleRes, transcript };
}

async function runChatPrompt(prompt) {
  const ready = await ensureChatGPTReady();
  if (!ready) throw new Error('ChatGPT tab is not ready');

  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: gptTabId },
    func: async (text) => {
      return window.sendPrompt ? window.sendPrompt(text) : '';
    },
    args: [prompt]
  });

  return result || '';
}

async function watchAndReact(url, like) {
  if (!ytWindowId) return;
  const tab = await chrome.tabs.create({ url, active: false, windowId: ytWindowId });

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (doLike) => {
      const vid = document.querySelector('video');
      if (vid) {
        vid.muted = true;
        vid.play();
      }

      setTimeout(() => {
        if (doLike) {
          document.querySelector('ytd-toggle-button-renderer button')?.click();
        } else {
          document.querySelector('ytd-menu-renderer button')?.click();
          setTimeout(() => {
            const item = Array.from(document.querySelectorAll('ytd-menu-service-item-renderer')).find((el) =>
              el.textContent.toLowerCase().includes('not interested')
            );
            item?.click();
          }, 400);
        }
      }, 2500);
    },
    args: [like]
  });

  setTimeout(() => chrome.tabs.remove(tab.id), 12000);
}

function cleanupTabs() {
  if (ytWindowId) chrome.windows.remove(ytWindowId);
  else if (ytTabId) chrome.tabs.remove(ytTabId);

  if (gptWindowId) chrome.windows.remove(gptWindowId);
  else if (gptTabId) chrome.tabs.remove(gptTabId);

  ytTabId = null;
  gptTabId = null;
  ytWindowId = null;
  gptWindowId = null;
}
