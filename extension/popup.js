document.getElementById('start').addEventListener('click', () => {
  chrome.runtime.sendMessage({cmd: 'start'});
});
document.getElementById('stop').addEventListener('click', () => {
  chrome.runtime.sendMessage({cmd: 'stop'});
});
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.status) {
    document.getElementById('status').textContent = msg.status;
  }
});
