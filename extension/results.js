document.addEventListener('DOMContentLoaded', async () => {
  const table = document.getElementById('table');
  const data = await chrome.storage.local.get('articles');
  const articles = data.articles || [];
  articles.sort((a,b) => (b.score?.overallQuality || 0) - (a.score?.overallQuality || 0));
  for (const v of articles) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${v.id}</td><td>${v.title || v.url}</td>` +
      `<td>${v.score?.overallQuality ?? ''}</td>` +
      `<td>${v.liked ? 'liked' : (v.disliked ? 'disliked' : '')}</td>` +
      `<td><a href="article.html?id=${v.id}">View</a></td>`;
    table.appendChild(tr);
  }
});
