let running = false;
let ytTabId = null;
let gptTabId = null;
let options = { count: 6, model: 'gpt-3.5-turbo' };

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.cmd === 'start') {
    options = Object.assign(options, msg.opts || {});
    startProcessing();
  } else if (msg.cmd === 'stop') {
    running = false;
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
    await fetch('http://localhost:5001/api/fetch', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, model: options.model})
    });
    done++;
    chrome.runtime.sendMessage({progress: Math.round(done/links.length*100), status: `processed ${done}/${links.length}`});
  }
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
