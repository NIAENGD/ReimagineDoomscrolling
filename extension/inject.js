document.addEventListener('click', e => {
  if (e.target.dataset.watchLike) {
    chrome.runtime.sendMessage({cmd: 'watchLike', url: e.target.dataset.url});
  } else if (e.target.dataset.watchDislike) {
    chrome.runtime.sendMessage({cmd: 'watchDislike', url: e.target.dataset.url});
  }
});
