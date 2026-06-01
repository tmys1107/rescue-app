async function initDetail() {
  const params = new URLSearchParams(location.search);
  const id = params.get('id');
  if (!id) { location.href = 'index.html'; return; }

  const data = await loadEquipment();
  const item = data.find(d => d.id === id);
  if (!item) { location.href = 'index.html'; return; }

  document.title = `${item.name} - 救助資器材学習アプリ`;
  document.getElementById('detail-name').textContent = item.name;
  document.getElementById('detail-category').textContent = item.category;

  // セクション表示制御ヘルパー
  const showSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.hidden = false;
  };
  const hideSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.hidden = true;
  };

  // 配置場所
  const locationEl = document.getElementById('detail-location');
  if (item.location) {
    locationEl.textContent = `📍 ${item.location}`;
  } else {
    locationEl.style.display = 'none';
  }

  // メイン画像
  const imgEl = document.getElementById('detail-image');
  if (item.image) {
    imgEl.src = item.image;
    imgEl.alt = item.name;
    imgEl.onerror = () => { imgEl.style.display = 'none'; };
  } else {
    imgEl.style.display = 'none';
  }

  // 諸元（重要項目はハイライト）
  const importantKeys = item.importantSpec || [];
  const table = document.getElementById('spec-table');
  Object.entries(item.spec).forEach(([key, val]) => {
    const tr = document.createElement('tr');
    if (importantKeys.includes(key)) {
      tr.className = 'spec-important';
    }
    const th = document.createElement('th');
    th.textContent = importantKeys.includes(key) ? `⭐ ${key}` : key;
    const td = document.createElement('td');
    td.textContent = val;
    tr.appendChild(th);
    tr.appendChild(td);
    table.appendChild(tr);
  });
  // 重要項目がない場合はヒントを隠す
  if (importantKeys.length === 0) {
    document.getElementById('spec-hint').style.display = 'none';
  }

  // 使用手順
  const list = document.getElementById('usage-list');
  item.usage.forEach(step => {
    const li = document.createElement('li');
    li.textContent = step;
    list.appendChild(li);
  });

  // 用途
  document.getElementById('purpose-text').textContent = item.purpose;

  // 実践ポイント
  const tipsList = document.getElementById('tips-list');
  if (item.tips && item.tips.length > 0) {
    showSection('sec-tips');
    item.tips.forEach(tip => {
      const card = document.createElement('div');
      card.className = 'tip-card';
      const titleEl = document.createElement('h3');
      titleEl.className = 'tip-title';
      titleEl.textContent = tip.title;
      const bodyEl = document.createElement('p');
      bodyEl.className = 'tip-body';
      bodyEl.textContent = tip.body;
      card.appendChild(titleEl);
      card.appendChild(bodyEl);
      const images = tip.images ?? (tip.image ? [tip.image] : []);
      images.forEach(src => {
        const img = document.createElement('img');
        img.src = src;
        img.alt = tip.title;
        img.className = 'tip-image';
        card.appendChild(img);
      });
      tipsList.appendChild(card);
    });
  }

  // 実務知見（出典行は除外・後方互換）
  const notesList = document.getElementById('notes-list');
  const userNotes = (item.notes || []).filter(n => !n.startsWith('出典：'));
  if (userNotes.length > 0) {
    showSection('sec-notes');
    userNotes.forEach(note => {
      const li = document.createElement('li');
      li.textContent = note;
      notesList.appendChild(li);
    });
  }

  // 参考資料（PDF等）
  const docsList = document.getElementById('docs-list');
  if (item.docs && item.docs.length > 0) {
    showSection('sec-docs');
    item.docs.forEach(doc => {
      const a = document.createElement('a');
      a.href = doc.file;
      a.target = '_blank';
      a.className = 'doc-link';
      a.textContent = doc.label;
      docsList.appendChild(a);
    });
  }

  // 目次ナビ：存在しないセクションへのリンクは隠す
  document.querySelectorAll('.detail-nav a').forEach(link => {
    const targetId = link.getAttribute('href').slice(1);
    const target = document.getElementById(targetId);
    if (!target || target.hidden) {
      link.style.display = 'none';
    }
  });

  // お気に入りボタン
  const favBtn = document.getElementById('fav-btn');
  const updateFavBtn = () => {
    favBtn.textContent = Storage.isFav(item.id) ? '★' : '☆';
    favBtn.classList.toggle('active', Storage.isFav(item.id));
  };
  updateFavBtn();
  favBtn.addEventListener('click', () => {
    Storage.toggleFav(item.id);
    updateFavBtn();
  });

  // 正答率
  const scoreSection = document.getElementById('score-section');
  const scoreDisplay = document.getElementById('score-display');
  const score = Storage.getScore(item.id);
  if (score) {
    scoreDisplay.innerHTML = `
      <div class="score-bar-wrap">
        <div class="score-bar" style="width:${score.pct}%"></div>
      </div>
      <span class="score-label">${score.correct}/${score.total}問 (${score.pct}%)</span>
    `;
  } else {
    scoreSection.style.display = 'none';
  }

  // 問題集ボタン
  document.getElementById('go-quiz-btn').addEventListener('click', () => {
    location.href = `index.html?quiz=1&itemId=${item.id}&name=${encodeURIComponent(item.name)}`;
  });
}

initDetail();
