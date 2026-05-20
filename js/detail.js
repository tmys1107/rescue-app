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

  // 諸元
  const table = document.getElementById('spec-table');
  Object.entries(item.spec).forEach(([key, val]) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<th>${key}</th><td>${val}</td>`;
    table.appendChild(tr);
  });

  // 使用手順
  const list = document.getElementById('usage-list');
  item.usage.forEach(step => {
    const li = document.createElement('li');
    li.textContent = step;
    list.appendChild(li);
  });

  // 用途
  document.getElementById('purpose-text').textContent = item.purpose;

  // 補足・注意事項
  const notesSection = document.getElementById('notes-section');
  const notesList = document.getElementById('notes-list');
  if (item.notes && item.notes.length > 0) {
    item.notes.forEach(note => {
      const li = document.createElement('li');
      li.textContent = note;
      notesList.appendChild(li);
    });
  } else {
    notesSection.style.display = 'none';
  }

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

  // 参考資料
  const docsSection = document.getElementById('docs-section');
  const docsList = document.getElementById('docs-list');
  if (item.docs && item.docs.length > 0) {
    item.docs.forEach(doc => {
      const a = document.createElement('a');
      a.href = doc.file;
      a.target = '_blank';
      a.className = 'doc-link';
      a.textContent = doc.label;
      docsList.appendChild(a);
    });
  } else {
    docsSection.style.display = 'none';
  }

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
