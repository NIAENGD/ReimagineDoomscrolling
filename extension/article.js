document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(location.search);
  const id = Number(params.get('id'));
  const resp = await fetch(`http://localhost:5001/api/article/${id}`);
  if (!resp.ok) return;
  const v = await resp.json();
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
  likeBtn.addEventListener('click', async () => {
    chrome.runtime.sendMessage({cmd: 'watchLike', url: v.url});
    v.liked = true; v.disliked = false;
    await fetch('http://localhost:5001/api/article', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(v)
    });
    likeBtn.disabled = true; dislikeBtn.disabled = false;
  });
  dislikeBtn.addEventListener('click', async () => {
    chrome.runtime.sendMessage({cmd: 'watchDislike', url: v.url});
    v.disliked = true; v.liked = false;
    await fetch('http://localhost:5001/api/article', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(v)
    });
    dislikeBtn.disabled = true; likeBtn.disabled = false;
  });
});
