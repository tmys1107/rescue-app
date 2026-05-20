async function initQuiz() {
  const quizArea = document.getElementById('quiz-area');
  const resultEl = document.getElementById('quiz-result');
  const categorySelect = document.getElementById('quiz-category-select');
  const struggleBtn = document.getElementById('struggle-btn');
  if (!quizArea) return;

  const urlParams = new URLSearchParams(location.search);
  const urlItemId = urlParams.get('itemId');
  const urlItemName = urlParams.get('name');

  const data = await loadEquipment();
  const categories = getCategories(data);
  let weakMode = false;

  if (urlItemId) {
    // 資器材個別モード：カテゴリ操作を隠してヘッダーを表示
    document.querySelector('.quiz-controls').style.display = 'none';
    const header = document.createElement('div');
    header.className = 'quiz-item-header';
    header.innerHTML = `
      <a href="javascript:history.back()" class="quiz-back-link">← 詳細に戻る</a>
      <span class="quiz-item-title">${urlItemName} の問題</span>
    `;
    quizArea.before(header);
  } else {
    categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      categorySelect.appendChild(opt);
    });

    const urlCat = urlParams.get('category');
    if (urlCat) categorySelect.value = urlCat;

    categorySelect.addEventListener('change', () => buildQuiz(data));

    struggleBtn.addEventListener('click', () => {
      weakMode = !weakMode;
      struggleBtn.classList.toggle('active', weakMode);
      buildQuiz(data);
    });
  }

  buildQuiz(data);

  function buildQuiz(data) {
    let filtered;
    if (urlItemId) {
      filtered = data.filter(d => d.id === urlItemId);
    } else {
      const cat = categorySelect.value;
      filtered = cat === 'all' ? data : data.filter(d => d.category === cat);
    }

    // 苦手モード：正答率60%未満の資器材に絞る
    if (weakMode) {
      const weakIds = Storage.getWeakItemIds();
      if (weakIds.length === 0) {
        quizArea.innerHTML = '<p class="empty-msg">苦手問題はまだありません。<br>問題を解いてから確認してください。</p>';
        resultEl.classList.add('hidden');
        return;
      }
      filtered = filtered.filter(d => weakIds.includes(d.id));
    }

    const questions = [];
    filtered.forEach(item => {
      item.quiz.forEach(q => {
        questions.push({ ...q, itemId: item.id, itemName: item.name });
      });
    });
    shuffle(questions);

    quizArea.innerHTML = '';
    resultEl.classList.add('hidden');

    if (questions.length === 0) {
      quizArea.innerHTML = '<p class="empty-msg">この条件の問題はまだありません。</p>';
      return;
    }

    let answered = 0;
    let correct = 0;

    questions.forEach((q, index) => {
      const card = document.createElement('div');
      card.className = 'quiz-card';
      card.innerHTML = `
        <div class="quiz-question">Q${index + 1}. ${q.question}</div>
        <div class="quiz-choices"></div>
        <div class="quiz-feedback hidden"></div>
      `;

      const choicesEl = card.querySelector('.quiz-choices');
      const feedbackEl = card.querySelector('.quiz-feedback');

      q.choices.forEach((choice, i) => {
        const btn = document.createElement('button');
        btn.className = 'choice-btn';
        btn.textContent = choice;
        btn.addEventListener('click', () => {
          if (btn.disabled) return;
          choicesEl.querySelectorAll('.choice-btn').forEach(b => b.disabled = true);

          const isCorrect = i === q.answer;
          btn.classList.add(isCorrect ? 'correct' : 'wrong');
          choicesEl.querySelectorAll('.choice-btn')[q.answer].classList.add('correct');

          feedbackEl.textContent = isCorrect ? '✓ 正解！' : `✗ 不正解。正解：${q.choices[q.answer]}`;
          feedbackEl.className = `quiz-feedback ${isCorrect ? 'correct' : 'wrong'}`;
          feedbackEl.classList.remove('hidden');

          // 正答率を保存
          Storage.recordAnswer(q.itemId, isCorrect);

          if (isCorrect) correct++;
          answered++;
          if (answered === questions.length) showResult(correct, questions.length);
        });
        choicesEl.appendChild(btn);
      });

      quizArea.appendChild(card);
    });
  }

  function showResult(correct, total) {
    const pct = Math.round(correct / total * 100);
    resultEl.innerHTML = `
      <h2>結果</h2>
      <div class="score">${correct} / ${total}</div>
      <p style="margin-top:8px;color:#666">${pct}% 正解</p>
      <button class="primary-btn" style="margin-top:20px" onclick="location.reload()">もう一度</button>
    `;
    resultEl.classList.remove('hidden');
    resultEl.scrollIntoView({ behavior: 'smooth' });
  }
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

initQuiz();
