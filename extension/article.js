document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(location.search);
  const id = Number(params.get('id'));
  const data = await chrome.storage.local.get('articles');
  const articles = data.articles || [];
  const v = articles.find(a => a.id === id);
  if (!v) return;
  document.getElementById('title').textContent = v.title || v.url;
  const table = document.getElementById('scores');
  const keys = ['logic','depth','insight','expression','inspiration','overallQuality'];
  for (const k of keys) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<th>${k}</th><td>${v.score?.[k] ?? ''}</td>`;
    table.appendChild(tr);
  }
  const tr = document.createElement('tr');
  tr.innerHTML = `<th>Blind Spots</th><td>${v.score?.blindSpots ?? ''}</td>`;
  table.appendChild(tr);
  document.getElementById('article').textContent = v.article || '';
  const likeBtn = document.getElementById('like');
  const dislikeBtn = document.getElementById('dislike');
  if (v.liked) likeBtn.disabled = true;
  if (v.disliked) dislikeBtn.disabled = true;
  likeBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({cmd: 'watchLike', url: v.url});
    v.liked = true; v.disliked = false;
    chrome.storage.local.set({articles});
    likeBtn.disabled = true; dislikeBtn.disabled = false;
  });
  dislikeBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({cmd: 'watchDislike', url: v.url});
    v.disliked = true; v.liked = false;
    chrome.storage.local.set({articles});
    dislikeBtn.disabled = true; likeBtn.disabled = false;
  });
});
