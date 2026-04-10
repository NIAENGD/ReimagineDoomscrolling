let allArticles = [];

const tableBody = document.querySelector('#table tbody');
const searchEl = document.getElementById('search');
const statusFilterEl = document.getElementById('statusFilter');
const sortByEl = document.getElementById('sortBy');
const statsEl = document.getElementById('stats');

function statusText(v) {
  if (v.liked) return 'liked';
  if (v.disliked) return 'disliked';
  return 'unrated';
}

function fmtDate(iso) {
  if (!iso) return '';
  const d = new Date(iso.replace(' ', 'T') + 'Z');
  return d.toLocaleString();
}

function renderStats(articles) {
  const liked = articles.filter((a) => a.liked).length;
  const disliked = articles.filter((a) => a.disliked).length;
  const avg = articles.length
    ? (articles.reduce((s, a) => s + Number(a.score?.overallQuality || 0), 0) / articles.length).toFixed(1)
    : '0.0';

  statsEl.innerHTML = [
    `<div class="stat"><span>Total</span><strong>${articles.length}</strong></div>`,
    `<div class="stat"><span>Liked</span><strong>${liked}</strong></div>`,
    `<div class="stat"><span>Disliked</span><strong>${disliked}</strong></div>`,
    `<div class="stat"><span>Avg quality</span><strong>${avg}</strong></div>`
  ].join('');
}

function renderRows(articles) {
  tableBody.innerHTML = '';

  for (const v of articles) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${v.id}</td>
      <td><div class="title-cell">${v.title || v.url}</div><div class="muted">${v.url}</div></td>
      <td>${v.score?.overallQuality ?? ''}</td>
      <td><span class="pill ${statusText(v)}">${statusText(v)}</span></td>
      <td>${fmtDate(v.updatedAt)}</td>
      <td><a href="article.html?id=${v.id}">View</a></td>`;
    tableBody.appendChild(tr);
  }
}

function applyFilters() {
  const q = searchEl.value.trim().toLowerCase();
  const statusFilter = statusFilterEl.value;
  const sortBy = sortByEl.value;

  let rows = allArticles.filter((a) => {
    const matchesQuery = !q || (a.title || '').toLowerCase().includes(q) || (a.url || '').toLowerCase().includes(q);
    const st = statusText(a);
    const matchesStatus = statusFilter === 'all' || st === statusFilter;
    return matchesQuery && matchesStatus;
  });

  if (sortBy === 'score') {
    rows.sort((a, b) => (Number(b.score?.overallQuality || 0) - Number(a.score?.overallQuality || 0)));
  } else if (sortBy === 'title') {
    rows.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
  } else {
    rows.sort((a, b) => (new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0)));
  }

  renderStats(rows);
  renderRows(rows);
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const resp = await fetch('http://localhost:5001/api/articles');
    const data = await resp.json();
    allArticles = data.articles || [];
    applyFilters();
  } catch (e) {
    tableBody.innerHTML = '<tr><td colspan="6">Failed to load articles from local server.</td></tr>';
  }

  [searchEl, statusFilterEl, sortByEl].forEach((el) => el.addEventListener('input', applyFilters));
});
