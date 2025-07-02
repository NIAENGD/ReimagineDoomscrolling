let running = false;
let ytTabId = null;
let gptTabId = null;
let ytWindowId = null;
let gptWindowId = null;
let options = { count: 6, scorePrompt: '', rewritePrompt: '' };
let articles = [];
chrome.storage.local.get('articles', data => { articles = data.articles || []; });

function log(msg) {
  chrome.runtime.sendMessage({ log: msg });
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

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.cmd === 'start') {
    options = Object.assign(options, msg.opts || {});
    startProcessing();
  } else if (msg.cmd === 'openTabs') {
    openTabs();
  } else if (msg.cmd === 'stop') {
    running = false;
    cleanupTabs();
  } else if (msg.cmd === 'watchLike') {
    watchAndReact(msg.url, true);
  } else if (msg.cmd === 'watchDislike') {
    watchAndReact(msg.url, false);
  }
});

async function startProcessing() {
  if (running) return;
  running = true;
  if (!ytTabId || !gptTabId) {
    await openTabs();
  }
  log('gathering links...');
  chrome.runtime.sendMessage({status: 'gathering links...', progress: 0});
  const links = await collectLinks(ytTabId, options.count);
  log('processing ' + links.length + ' videos');
  chrome.runtime.sendMessage({status: 'processing ' + links.length + ' videos', progress: 0});
  let done = 0;
  for (const url of links) {
    if (!running) break;
    try {
      const title = await fetchTitle(url);
      log('processing video: ' + title);
      const transcript = await fetchTranscript(url);
      const result = await processTranscript(transcript, title);
      const article = {id: articles.length + 1, url, title, ...result};
      await persistArticle(article);
      articles.push(article);
    } catch (e) {
      console.error('Error processing video', url, e);
      log('error: ' + e.message);
    }
    done++;
    chrome.runtime.sendMessage({progress: Math.round(done/links.length*100), status: `processed ${done}/${links.length}`});
  }
  chrome.storage.local.set({articles});
  log('done');
  chrome.runtime.sendMessage({status: 'done', progress: 100});
  running = false;
  cleanupTabs();
}

function openTab(url) {
  return new Promise(resolve => {
    chrome.tabs.create({url, active: false}, tab => resolve(tab.id));
  });
}

// open a minimised popup window for a URL, returning both window and tab ids
function openPopup(url) {
  return new Promise(resolve => {
    chrome.windows.create({
      url,
      type: 'popup',
      focused: true,
      state: 'normal'
    }, win => {
      resolve({ windowId: win.id, tabId: win.tabs[0].id });
    });
  });
}

// wait until the tab finishes loading
function waitTabComplete(tabId) {
  return new Promise(resolve => {
    const listener = (id, info) => {
      if (id === tabId && info.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
  });
}

async function openTabs() {
  cleanupTabs();
  const yt = await openPopup('https://www.youtube.com');
  ytWindowId = yt.windowId;
  ytTabId = yt.tabId;
  const gpt = await openPopup('https://chatgpt.com');
  gptWindowId = gpt.windowId;
  gptTabId = gpt.tabId;
}

async function collectLinks(tabId, count) {
  let links = [];
  for (let i = 0; i < 20 && links.length < count; i++) {
    const res = await chrome.scripting.executeScript({
      target: {tabId},
      func: already => {
        function getFrontPageVideos() {
          const urls = [];
          const grid = document.querySelector('ytd-rich-grid-renderer');
          if (!grid) return urls;
          grid.querySelectorAll('ytd-rich-item-renderer, ytd-reel-video-renderer, ytd-display-ad-renderer')
            .forEach(tile => {
              if (tile.tagName.includes('DISPLAY-AD') ||
                  tile.tagName.includes('PROMOTED') ||
                  tile.querySelector('[badge-style-type="ad"], span')?.textContent === 'Ad') return;
              const link = tile.querySelector('a#thumbnail[href]');
              if (!link) return;
              if (link.getAttribute('href').startsWith('/shorts/')) return;
              const url = new URL(link.getAttribute('href'), 'https://www.youtube.com').href;
              if (!already.includes(url)) urls.push(url);
            });
          return urls;
        }
        window.scrollBy(0, window.innerHeight);
        return getFrontPageVideos();
      },
      args: [links],
    });
    const newLinks = (res[0] && res[0].result) || [];
    for (const u of newLinks) {
      if (!links.includes(u)) {
        links.push(u);
        log('link gathered: ' + u);
      }
    }
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
  const { windowId, tabId } = await openPopup(url);
  await waitTabComplete(tabId);
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => document.title || ''
    });
    return result || url;
  } finally {
    chrome.windows.remove(windowId);
  }
}

async function processTranscript(transcript, title) {
  log('scoring: ' + title);
  const scorePrompt = `${options.scorePrompt}\n\n${transcript}`;
  const scoreRes = await runChatPrompt(scorePrompt);
  let score = {};
  try { score = JSON.parse(scoreRes); } catch (e) {}
  log('rewriting: ' + title);
  const articleRes = await runChatPrompt(`${options.rewritePrompt}\n\n${transcript}`);
  return { score, article: articleRes, transcript };
}

async function runChatPrompt(prompt) {
  const res = await chrome.scripting.executeScript({
    target: { tabId: gptTabId },
    func: async (p) => {
      const maybeNewChatBtn = document.querySelector('a[data-testid="create-new-chat-button"]');
      if (window.location.pathname === '/' && maybeNewChatBtn) {
        maybeNewChatBtn.click();
      }
      if (window.sendPrompt) {
        return await window.sendPrompt(p);
      }
      return '';
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

function cleanupTabs() {
  if (ytWindowId) {
    chrome.windows.remove(ytWindowId);
  } else if (ytTabId) {
    chrome.tabs.remove(ytTabId);
  }
  if (gptWindowId) {
    chrome.windows.remove(gptWindowId);
  } else if (gptTabId) {
    chrome.tabs.remove(gptTabId);
  }
  ytTabId = null;
  ytWindowId = null;
  gptTabId = null;
  gptWindowId = null;
}
