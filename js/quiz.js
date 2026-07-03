async function initQuiz() {
  const quizArea = document.getElementById('quiz-area');
  const resultEl = document.getElementById('quiz-result');
  const categorySelect = document.getElementById('quiz-category-select');
  const struggleBtn = document.getElementById('struggle-btn');
  if (!quizArea) return;

  quizArea.innerHTML = '<p class="loading-msg">読み込み中…</p>';

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
    const backLink = document.createElement('a');
    backLink.className = 'quiz-back-link';
    backLink.href = '#';
    backLink.textContent = '← 詳細に戻る';
    backLink.addEventListener('click', (e) => { e.preventDefault(); history.back(); });
    const titleSpan = document.createElement('span');
    titleSpan.className = 'quiz-item-title';
    titleSpan.textContent = `${urlItemName} の問題`;
    header.appendChild(backLink);
    header.appendChild(titleSpan);
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
      item.quiz.forEach((q, idx) => {
        // qid 未設定の問題はitemIdから自動生成（後方互換）
        const qid = q.qid || `${item.id}-q${idx + 1}`;
        questions.push({ ...q, qid, itemId: item.id, itemName: item.name });
      });
    });
    shuffle(questions);

    quizArea.innerHTML = '';
    resultEl.classList.add('hidden');

    if (questions.length === 0) {
      quizArea.innerHTML = '<p class="empty-msg">この条件の問題はまだありません。</p>';
      return;
    }

    // 1問ずつ出題
    let index = 0;
    let correct = 0;
    showQuestion();

    function showQuestion() {
      quizArea.innerHTML = '';
      const q = questions[index];
      const isLast = index === questions.length - 1;

      const card = document.createElement('div');
      card.className = 'quiz-card';

      const head = document.createElement('div');
      head.className = 'quiz-question';
      const prog = document.createElement('span');
      prog.className = 'quiz-progress';
      prog.textContent = `${index + 1} / ${questions.length}　${q.itemName}`;
      const qText = document.createElement('div');
      qText.textContent = `Q${index + 1}. ${q.question}`;
      head.appendChild(prog);
      head.appendChild(qText);

      const choicesEl = document.createElement('div');
      choicesEl.className = 'quiz-choices';
      const feedbackEl = document.createElement('div');
      feedbackEl.className = 'quiz-feedback hidden';

      const nextBtn = document.createElement('button');
      nextBtn.className = 'primary-btn quiz-next-btn hidden';
      nextBtn.textContent = isLast ? '結果を見る' : '次の問題 →';
      nextBtn.addEventListener('click', () => {
        if (isLast) {
          quizArea.innerHTML = '';
          showResult(correct, questions.length);
        } else {
          index++;
          showQuestion();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });

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

          // フィードバック組み立て
          feedbackEl.innerHTML = '';
          const resultLine = document.createElement('div');
          resultLine.className = 'quiz-result-line';
          resultLine.textContent = isCorrect ? '✓ 正解！' : `✗ 不正解。正解：${q.choices[q.answer]}`;
          feedbackEl.appendChild(resultLine);

          if (q.explanation) {
            const expEl = document.createElement('div');
            expEl.className = 'quiz-explanation';
            expEl.textContent = q.explanation;
            feedbackEl.appendChild(expEl);
          }

          feedbackEl.className = `quiz-feedback ${isCorrect ? 'correct' : 'wrong'}`;
          feedbackEl.classList.remove('hidden');

          // 正答率を保存（資器材単位・問題単位の両方）
          Storage.recordAnswer(q.itemId, isCorrect);
          Storage.recordQuestionAnswer(q.qid, isCorrect);

          if (isCorrect) correct++;
          nextBtn.classList.remove('hidden');
        });
        choicesEl.appendChild(btn);
      });

      card.appendChild(head);
      card.appendChild(choicesEl);
      card.appendChild(feedbackEl);
      card.appendChild(nextBtn);
      quizArea.appendChild(card);
    }
  }

  function showResult(correct, total) {
    const pct = Math.round(correct / total * 100);
    resultEl.innerHTML = `
      <h2>結果</h2>
      <div class="score">${correct} / ${total}</div>
      <p class="quiz-result-pct">${pct}% 正解</p>
      <button class="primary-btn quiz-retry-btn" onclick="location.reload()">もう一度</button>
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
