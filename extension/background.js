let running = false;
let ytTabId = null;
let gptTabId = null;

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.cmd === 'start') {
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
  chrome.runtime.sendMessage({status: 'gathering links...'});
  const links = await collectLinks(ytTabId);
  chrome.runtime.sendMessage({status: 'processing ' + links.length + ' videos'});
  for (const url of links) {
    if (!running) break;
    await fetch('http://localhost:5001/api/fetch', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url})
    });
  }
  chrome.runtime.sendMessage({status: 'done'});
}

function openTab(url) {
  return new Promise(resolve => {
    chrome.tabs.create({url, active: false}, tab => resolve(tab.id));
  });
}

function collectLinks(tabId) {
  return chrome.scripting.executeScript({
    target: {tabId},
    func: () => {
      const anchors = Array.from(document.querySelectorAll('a#thumbnail'));
      const hrefs = anchors.map(a => a.href).filter(u => u.includes('watch'));
      return hrefs.slice(0, 6);
    }
  }).then(res => res[0].result || []);
}
