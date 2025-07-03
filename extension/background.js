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

chrome.commands.onCommand.addListener((command) => {
  if (command === 'stop-processing') {
    running = false;
    cleanupTabs();
    fetch('http://localhost:5001/shutdown', { method: 'POST' }).catch(() => {});
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

function openTab(url, windowId = null) {
  return new Promise(resolve => {
    chrome.tabs.create({ url, active: false, windowId }, tab => resolve(tab.id));
  });
}

// open a popup window or tab. if opts.windowId is provided a new tab is opened
// in that window instead of creating a new window. otherwise a popup window is
// created with optional positioning.
function openPopup(url, opts = {}) {
  return new Promise(resolve => {
    if (opts.windowId) {
      chrome.tabs.create({ url, active: false, windowId: opts.windowId }, tab => {
        resolve({ windowId: opts.windowId, tabId: tab.id, createdWindow: false });
      });
    } else {
      chrome.windows.create({
        url,
        type: 'popup',
        focused: true,
        state: 'normal',
        left: opts.left,
        top: opts.top,
        width: opts.width,
        height: opts.height
      }, win => {
        resolve({ windowId: win.id, tabId: win.tabs[0].id, createdWindow: true });
      });
    }
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

// ensure ChatGPT content script has loaded
async function ensureChatGPTReady() {
  for (let i = 0; i < 40; i++) {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: gptTabId },
      func: () => Boolean(window.sendPrompt)
    });
    if (result) return true;
    await new Promise(r => setTimeout(r, 500));
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
}

async function collectLinks(tabId, count) {
  function gather(already = []) {
    return chrome.scripting.executeScript({
      target: { tabId },
      func: (seen) => {
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
            if (!seen.includes(url)) urls.push(url);
          });
        return urls;
      },
      args: [already],
    }).then(res => (res[0] && res[0].result) || []);
  }

  let links = await gather();
  if (links.length < count) {
    await chrome.scripting.executeScript({ target: { tabId }, func: () => window.scrollBy(0, window.innerHeight) });
    await new Promise(r => setTimeout(r, 1000));
    const more = await gather(links);
    for (const u of more) {
      if (!links.includes(u)) {
        links.push(u);
        log('link gathered: ' + u);
      }
    }
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
  const popup = await openPopup(url, ytWindowId ? { windowId: ytWindowId } : {});
  await waitTabComplete(popup.tabId);
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: popup.tabId },
      func: () => document.title || ''
    });
    return result || url;
  } finally {
    if (popup.createdWindow) {
      chrome.windows.remove(popup.windowId);
    } else {
      chrome.tabs.remove(popup.tabId);
    }
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
  const ready = await ensureChatGPTReady();
  if (!ready) throw new Error('ChatGPT not ready');
  const [{ result: coords }] = await chrome.scripting.executeScript({
    target: { tabId: gptTabId },
    func: () => {
      const newBtn = document.querySelector(
        [
          'a[data-testid^="create-new-chat"]',
          'button[data-testid^="new-chat"]',
          'button[aria-label="New chat"]',
          'a[href="/new"]'
        ].join(', ')
      );
      const compSel = [
        'div[contenteditable="true"].ProseMirror',
        'textarea[data-testid="prompt-textarea"]',
        'textarea[name="prompt-textarea"]',
        'textarea[data-id="prompt-textarea"]',
        'textarea[placeholder*="Ask"]'
      ].join(', ');
      const composer = document.querySelector(compSel);
      const send = composer?.closest('form')?.querySelector(
        [
          'button[data-testid="send-button"]',
          'button[aria-label^="Send"]',
          'button svg[data-testid="send"]'
        ].join(', ')
      );
      function pos(el) {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: window.screenX + r.left + r.width / 2, y: window.screenY + r.top + r.height / 2 };
      }
      return { newChat: window.location.pathname === '/' ? pos(newBtn) : null, composer: pos(composer), send: pos(send) };
    }
  });

  async function post(url, body) {
    await fetch('http://localhost:5001' + url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  }

  if (coords.newChat) {
    await post('/api/click', coords.newChat);
    await new Promise(r => setTimeout(r, 500));
  }
  if (coords.composer) {
    await post('/api/click', coords.composer);
    await post('/api/type', { text: prompt });
  }
  if (coords.send) {
    await post('/api/click', coords.send);
  }

  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: gptTabId },
    func: () => window.waitAssistantReply && window.waitAssistantReply()
  });
  return result || '';
}

async function watchAndReact(url, like) {
  const id = await openTab(url, ytWindowId);
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
