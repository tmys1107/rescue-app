// ===== 復習間隔（忘却曲線に合わせて延ばす） =====
// 連続正解が伸びるほど次に出るまでを長くする。間違えたら翌日に戻す。
const REVIEW_DAYS = [1, 3, 7, 14, 30, 60];
const DAY_MS = 24 * 60 * 60 * 1000;

function nextDueAt(streak, now) {
  const days = REVIEW_DAYS[Math.min(streak, REVIEW_DAYS.length - 1)];
  return now + days * DAY_MS;
}

// 習得ライン：全問に1回以上答えていて、かつ正答率80%以上
const MASTERY_ACCURACY = 0.8;

// ===== LocalStorage ユーティリティ =====
// プライベートブラウズ・容量超過・保存拒否でも画面が止まらないよう、
// 読み書きは必ず例外を飲み込む（保存できなくても出題は続けられる）。
function lsRead(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    const val = JSON.parse(raw);
    if (val === null || typeof val !== 'object') return fallback;
    return val;
  } catch (e) {
    console.warn(`${key} を読めなかったので初期値を使います`, e);
    return fallback;
  }
}

function lsWrite(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    console.warn(`${key} を保存できませんでした`, e);
    return false;
  }
}

const Storage = {
  getFavs: () => lsRead('favs', []),
  setFavs: (arr) => lsWrite('favs', arr),
  toggleFav(id) {
    const favs = this.getFavs();
    const idx = favs.indexOf(id);
    if (idx === -1) favs.push(id); else favs.splice(idx, 1);
    this.setFavs(favs);
    return idx === -1;
  },
  isFav: (id) => Storage.getFavs().includes(id),

  // 資器材単位の累計: { [itemId]: { correct, total } }
  // 習得判定には使わない（1問だけ正解でも100%になるため）。
  // qid単位の記録が無かった頃のデータを残すために書き続けている。
  getScores: () => lsRead('scores', {}),
  recordAnswer(itemId, isCorrect) {
    const scores = this.getScores();
    if (!scores[itemId]) scores[itemId] = { correct: 0, total: 0 };
    scores[itemId].total++;
    if (isCorrect) scores[itemId].correct++;
    lsWrite('scores', scores);
  },
  getScore(itemId) {
    const s = this.getScores()[itemId];
    if (!s || s.total === 0) return null;
    return { correct: s.correct, total: s.total, pct: Math.round(s.correct / s.total * 100) };
  },

  // ===== 問題ごとの記録（qid単位） =====
  // { [qid]: { correct, total, streak, last, due } }
  getQuestionScores: () => lsRead('questionScores', {}),
  recordQuestionAnswer(qid, isCorrect) {
    if (!qid) return;
    const scores = this.getQuestionScores();
    const s = scores[qid] || { correct: 0, total: 0, streak: 0 };
    s.total++;
    if (isCorrect) {
      s.correct++;
      s.streak = (s.streak || 0) + 1;
    } else {
      s.streak = 0;
    }
    const now = Date.now();
    s.last = now;
    s.due = nextDueAt(s.streak, now);
    scores[qid] = s;
    lsWrite('questionScores', scores);
  },
};

// 問題の一意キー。JSONにqidがあればそれを使う（並べ替えても履歴が追従する）
function qidOf(item, q, idx) {
  return q.qid || `${item.id}-q${idx + 1}`;
}

// 資器材・操法1件の習得状況。
// 「網羅率（何問に答えたか）」と「正答率」の両方を見るのが肝。
// 累計正答率だけだと、7問中1問正解しただけで習得100%になってしまう。
function getMastery(item, now = Date.now()) {
  const quiz = item.quiz || [];
  if (quiz.length === 0) return null;

  const all = Storage.getQuestionScores();
  let answered = 0, correct = 0, total = 0, due = 0;

  quiz.forEach((q, i) => {
    const s = all[qidOf(item, q, i)];
    if (!s || !s.total) return;
    answered++;
    correct += s.correct;
    total += s.total;
    if (s.due && s.due <= now) due++;
  });

  if (answered === 0) {
    // qid単位の記録が無い場合だけ、旧来の資器材単位の記録で代用する
    const legacy = Storage.getScore(item.id);
    if (!legacy) return null;
    return {
      questions: quiz.length, answered: 0, due: 0, legacy: true,
      coveragePct: 0, accuracy: legacy.correct / legacy.total,
      pct: legacy.pct, mastered: false
    };
  }

  const accuracy = correct / total;
  return {
    questions: quiz.length,
    answered,
    due,
    legacy: false,
    coveragePct: Math.round(answered / quiz.length * 100),
    accuracy,
    pct: Math.round(accuracy * 100),
    // 四捨五入前の値で判定する（79.5%が80%に化けて習得にならないように）
    mastered: answered === quiz.length && accuracy >= MASTERY_ACCURACY
  };
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

// 苦手の判定：1回以上答えていて正答率60%未満
const WEAK_ACCURACY = 0.6;

function isWeakQid(qid) {
  const s = Storage.getQuestionScores()[qid];
  return !!s && s.total >= 1 && (s.correct / s.total) < WEAK_ACCURACY;
}

// 出題順を決める。期限が来たもの → 未回答 → それ以外、の順。
// 期限を過ぎて長いものほど先に出す。同じ段のなかはシャッフル。
function sortForStudy(questions, now = Date.now()) {
  const all = Storage.getQuestionScores();
  const due = [], fresh = [], rest = [];

  questions.forEach(q => {
    const s = all[q.qid];
    if (!s || !s.total) fresh.push(q);
    else if (s.due && s.due <= now) due.push({ q, over: now - s.due });
    else rest.push(q);
  });

  due.sort((a, b) => b.over - a.over);
  shuffle(fresh);
  shuffle(rest);
  return [...due.map(d => d.q), ...fresh, ...rest];
}

// カードや詳細に出すバッジの文言と色
function masteryBadge(m) {
  if (!m) return { cls: 'none', text: '未学習' };
  if (m.legacy) return { cls: 'learning', text: `学習中 ${m.pct}%` };
  if (m.answered < m.questions) {
    return { cls: 'learning', text: `学習中 ${m.answered}/${m.questions}問` };
  }
  if (m.due > 0) return { cls: 'due', text: `要復習 ${m.pct}%` };
  if (m.mastered) return { cls: 'done', text: `習得 ${m.pct}%` };
  return { cls: 'learning', text: `あと一歩 ${m.pct}%` };
}

// ===== データ取得 =====
async function loadEquipment() {
  const res = await fetch('data/equipment.json');
  return res.json();
}

// カテゴリは件数の多い順に並べる。
// 登録順だと1件しかないカテゴリが先頭に来て、絞り込みが使いにくい。
function getCategories(data) {
  const count = new Map();
  data.forEach(d => count.set(d.category, (count.get(d.category) || 0) + 1));
  return [...count.keys()].sort((a, b) => count.get(b) - count.get(a));
}

const TYPE_EQ = '資器材';
const TYPE_OPS = '操法・訓練';

// 種別（資器材／操法）で絞る。type 未設定の古いデータは資器材として扱う
function byType(data, type) {
  return data.filter(d => (d.type || TYPE_EQ) === type);
}

// ===== index.html 初期化 =====
async function initIndex() {
  const data = await loadEquipment();

  // 資器材タブと操法タブは作りが同じなので、同じ関数で組む
  initListTab({
    data: byType(data, TYPE_EQ),
    gridId: 'card-grid',
    filterId: 'category-filter',
    searchId: 'search-input',
    emptyMsg: '該当する資器材はありません。'
  });
  initListTab({
    data: byType(data, TYPE_OPS),
    gridId: 'ops-card-grid',
    filterId: 'ops-category-filter',
    searchId: 'ops-search-input',
    emptyMsg: '該当する操法・訓練はありません。'
  });

  // お気に入りは種別をまたぐ（表示時に毎回再描画）
  renderFavGrid(data);
  document.querySelector('[data-tab="fav"]').addEventListener('click', () => renderFavGrid(data));

  // URLパラメータでタブを開く（?tab=ops など。?quiz=1 は従来互換）
  const params = new URLSearchParams(location.search);
  const openTab = params.get('quiz') === '1' ? 'quiz' : params.get('tab');
  if (openTab) {
    const btn = document.querySelector(`[data-tab="${CSS.escape(openTab)}"]`);
    if (btn) btn.click();
  }
}

// 一覧タブ（検索＋カテゴリフィルター＋カード）を1つ組み立てる
function initListTab({ data, gridId, filterId, searchId, emptyMsg }) {
  const filterEl = document.getElementById(filterId);
  const searchInput = document.getElementById(searchId);
  if (!filterEl || !searchInput) return;

  const categories = getCategories(data);
  let activeCategory = 'all';

  const update = () => {
    let filtered = activeCategory === 'all'
      ? data
      : data.filter(d => d.category === activeCategory);
    if (searchInput.value) filtered = filtered.filter(d => matchesQuery(d, searchInput.value));
    renderCards(filtered, gridId, emptyMsg);
  };

  const select = (cat) => {
    activeCategory = cat;
    filterEl.querySelectorAll('.cat-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.cat === cat);
    });
    update();
  };

  filterEl.appendChild(createCatBtn('すべて', 'all', true, () => select('all')));
  categories.forEach(cat => {
    filterEl.appendChild(createCatBtn(cat, cat, false, () => select(cat)));
  });

  // カテゴリが1つだけならフィルターは意味がないので出さない
  if (categories.length <= 1) filterEl.style.display = 'none';

  searchInput.addEventListener('input', update);
  update();
}

// 名前・カテゴリ・用途・手順・実務知見・諸元を横断検索
function matchesQuery(d, query) {
  const q = query.toLowerCase();
  const targets = [
    d.name,
    d.category,
    d.purpose || '',
    ...(d.usage || []),
    ...(d.notes || []),
    ...Object.entries(d.spec || {}).flat()
  ];
  return targets.some(t => String(t).toLowerCase().includes(q));
}

function createCatBtn(label, cat, isActive, onClick) {
  const btn = document.createElement('button');
  btn.className = 'cat-btn' + (isActive ? ' active' : '');
  btn.textContent = label;
  btn.dataset.cat = cat;
  btn.addEventListener('click', onClick);
  return btn;
}

function renderCards(data, gridId = 'card-grid', emptyMsg = '該当する資器材はありません。') {
  const grid = document.getElementById(gridId);
  if (!grid) return;
  grid.textContent = '';
  if (data.length === 0) {
    const p = document.createElement('p');
    p.className = 'empty-msg';
    p.textContent = emptyMsg;
    grid.appendChild(p);
    return;
  }
  data.forEach(item => grid.appendChild(buildCard(item)));
}

// カード1枚を生成（一覧・お気に入り共通）
function buildCard(item) {
  const a = document.createElement('a');
  a.className = 'card';
  a.href = `detail.html?id=${item.id}`;

  const makePlaceholder = () => {
    const ph = document.createElement('div');
    ph.className = 'card-thumb card-thumb-placeholder';
    ph.textContent = item.category.charAt(0);
    return ph;
  };

  if (item.image) {
    const img = document.createElement('img');
    img.className = 'card-thumb';
    img.src = item.image;
    img.alt = item.name;
    img.loading = 'lazy';
    img.onerror = () => { img.replaceWith(makePlaceholder()); };
    a.appendChild(img);
  } else if (item.type !== TYPE_OPS) {
    // 操法は撮るべき「物」が無いので、空の枠は出さずカードを詰める
    a.appendChild(makePlaceholder());
  } else {
    a.classList.add('card-noimage');
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

  // 習得状況バッジ（全問に答えて正答率80%以上で「習得」）
  const badge = masteryBadge(getMastery(item));
  const progress = document.createElement('div');
  progress.className = `card-progress ${badge.cls}`;
  progress.textContent = badge.text;
  body.appendChild(progress);

  a.appendChild(body);

  if (Storage.isFav(item.id)) {
    const star = document.createElement('span');
    star.className = 'card-fav-mark';
    star.textContent = '★';
    a.appendChild(star);
  }

  return a;
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
  favItems.forEach(item => grid.appendChild(buildCard(item)));
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
