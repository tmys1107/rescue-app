// ===== LocalStorage ユーティリティ =====
const Storage = {
  getFavs: () => JSON.parse(localStorage.getItem('favs') || '[]'),
  setFavs: (arr) => localStorage.setItem('favs', JSON.stringify(arr)),
  toggleFav(id) {
    const favs = this.getFavs();
    const idx = favs.indexOf(id);
    if (idx === -1) favs.push(id); else favs.splice(idx, 1);
    this.setFavs(favs);
    return idx === -1;
  },
  isFav: (id) => Storage.getFavs().includes(id),

  // 正答率: { [itemId]: { correct: N, total: N } }
  getScores: () => JSON.parse(localStorage.getItem('scores') || '{}'),
  recordAnswer(itemId, isCorrect) {
    const scores = this.getScores();
    if (!scores[itemId]) scores[itemId] = { correct: 0, total: 0 };
    scores[itemId].total++;
    if (isCorrect) scores[itemId].correct++;
    localStorage.setItem('scores', JSON.stringify(scores));
  },
  getScore(itemId) {
    const s = this.getScores()[itemId];
    if (!s || s.total === 0) return null;
    return { correct: s.correct, total: s.total, pct: Math.round(s.correct / s.total * 100) };
  },
  // 正答率が低い問題IDを返す（total>=1 かつ pct<60）
  getWeakItemIds() {
    const scores = this.getScores();
    return Object.entries(scores)
      .filter(([, s]) => s.total >= 1 && (s.correct / s.total) < 0.6)
      .map(([id]) => id);
  }
};

// ===== データ取得 =====
async function loadEquipment() {
  const res = await fetch('data/equipment.json');
  return res.json();
}

function getCategories(data) {
  return [...new Set(data.map(d => d.category))];
}

// ===== index.html 初期化 =====
async function initIndex() {
  const data = await loadEquipment();
  const categories = getCategories(data);
  let activeCategory = 'all';

  // カテゴリフィルター
  const filterEl = document.getElementById('category-filter');
  const allBtn = createCatBtn('すべて', 'all', true, () => {
    activeCategory = 'all';
    updateFilter(data, activeCategory, searchInput.value);
    setActiveCatBtn('all');
  });
  filterEl.appendChild(allBtn);

  categories.forEach(cat => {
    const btn = createCatBtn(cat, cat, false, () => {
      activeCategory = cat;
      updateFilter(data, activeCategory, searchInput.value);
      setActiveCatBtn(cat);
    });
    filterEl.appendChild(btn);
  });

  // 検索
  const searchInput = document.getElementById('search-input');
  searchInput.addEventListener('input', () => {
    updateFilter(data, activeCategory, searchInput.value);
  });

  // お気に入りタブ（表示時に毎回再描画）
  renderFavGrid(data);
  document.querySelector('[data-tab="fav"]').addEventListener('click', () => renderFavGrid(data));

  // 初期表示
  renderCards(data);

  // URLパラメータで問題集タブを開く
  if (new URLSearchParams(location.search).get('quiz') === '1') {
    document.querySelector('[data-tab="quiz"]').click();
  }

  function setActiveCatBtn(cat) {
    filterEl.querySelectorAll('.cat-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.cat === cat);
    });
  }

  function updateFilter(data, cat, query) {
    let filtered = cat === 'all' ? data : data.filter(d => d.category === cat);
    if (query) filtered = filtered.filter(d => d.name.includes(query));
    renderCards(filtered);
  }
}

function createCatBtn(label, cat, isActive, onClick) {
  const btn = document.createElement('button');
  btn.className = 'cat-btn' + (isActive ? ' active' : '');
  btn.textContent = label;
  btn.dataset.cat = cat;
  btn.addEventListener('click', onClick);
  return btn;
}

function renderCards(data) {
  const grid = document.getElementById('card-grid');
  grid.innerHTML = '';
  if (data.length === 0) {
    grid.innerHTML = '<p class="empty-msg">該当する資器材はありません。</p>';
    return;
  }
  data.forEach(item => {
    const a = document.createElement('a');
    a.className = 'card';
    a.href = `detail.html?id=${item.id}`;

    if (item.image) {
      const img = document.createElement('img');
      img.className = 'card-thumb';
      img.src = item.image;
      img.alt = item.name;
      img.loading = 'lazy';
      img.onerror = () => { img.style.display = 'none'; };
      a.appendChild(img);
    }

    const body = document.createElement('div');
    body.className = 'card-body';
    const cat = document.createElement('div');
    cat.className = 'card-category';
    cat.textContent = item.category;
    const name = document.createElement('div');
    name.className = 'card-name';
    name.textContent = item.name;
    body.appendChild(cat);
    body.appendChild(name);
    a.appendChild(body);

    if (Storage.isFav(item.id)) {
      const star = document.createElement('span');
      star.className = 'card-fav-mark';
      star.textContent = '★';
      a.appendChild(star);
    }

    grid.appendChild(a);
  });
}

function renderFavGrid(data) {
  const grid = document.getElementById('fav-grid');
  const emptyMsg = document.getElementById('fav-empty');
  if (!grid) return;
  const favIds = Storage.getFavs();
  const favItems = data.filter(d => favIds.includes(d.id));
  grid.innerHTML = '';
  if (favItems.length === 0) {
    emptyMsg.classList.remove('hidden');
    return;
  }
  emptyMsg.classList.add('hidden');
  favItems.forEach(item => {
    const a = document.createElement('a');
    a.className = 'card';
    a.href = `detail.html?id=${item.id}`;

    if (item.image) {
      const img = document.createElement('img');
      img.className = 'card-thumb';
      img.src = item.image;
      img.alt = item.name;
      img.loading = 'lazy';
      img.onerror = () => { img.style.display = 'none'; };
      a.appendChild(img);
    }

    const body = document.createElement('div');
    body.className = 'card-body';
    const cat = document.createElement('div');
    cat.className = 'card-category';
    cat.textContent = item.category;
    const name = document.createElement('div');
    name.className = 'card-name';
    name.textContent = item.name;
    body.appendChild(cat);
    body.appendChild(name);
    a.appendChild(body);

    const star = document.createElement('span');
    star.className = 'card-fav-mark';
    star.textContent = '★';
    a.appendChild(star);

    grid.appendChild(a);
  });
}

// ===== タブ切り替え =====
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
  });
}

// ===== ページ判定 =====
if (document.getElementById('card-grid')) {
  initTabs();
  initIndex();
}
