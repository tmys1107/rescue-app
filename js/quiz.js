async function initQuiz() {
  const quizArea = document.getElementById('quiz-area');
  const resultEl = document.getElementById('quiz-result');
  const categorySelect = document.getElementById('quiz-category-select');
  const typeSelect = document.getElementById('quiz-type-select');
  const countSelect = document.getElementById('quiz-count-select');
  const struggleBtn = document.getElementById('struggle-btn');
  if (!quizArea) return;

  quizArea.innerHTML = '<p class="loading-msg">読み込み中…</p>';

  const urlParams = new URLSearchParams(location.search);
  const urlItemId = urlParams.get('itemId');
  const urlItemName = urlParams.get('name');

  const data = await loadEquipment();
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
    // 種別で絞ったうえで、その中にあるカテゴリだけを選択肢に出す
    const fillCategories = () => {
      const scoped = typeSelect && typeSelect.value !== 'all'
        ? byType(data, typeSelect.value)
        : data;
      categorySelect.textContent = '';
      const allOpt = document.createElement('option');
      allOpt.value = 'all';
      allOpt.textContent = 'すべて';
      categorySelect.appendChild(allOpt);
      getCategories(scoped).forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat;
        categorySelect.appendChild(opt);
      });
    };
    fillCategories();

    const urlCat = urlParams.get('category');
    if (urlCat) categorySelect.value = urlCat;

    if (typeSelect) {
      typeSelect.addEventListener('change', () => {
        fillCategories();           // 種別を変えるとカテゴリは「すべて」に戻る
        buildQuiz(data);
      });
    }

    categorySelect.addEventListener('change', () => buildQuiz(data));
    if (countSelect) countSelect.addEventListener('change', () => buildQuiz(data));

    struggleBtn.addEventListener('click', () => {
      weakMode = !weakMode;
      struggleBtn.classList.toggle('active', weakMode);
      buildQuiz(data);
    });
  }

  buildQuiz(data);

  // 1回の出題数。資器材個別モードはその資器材の全問を出す（上限なし）
  function sessionLimit() {
    if (urlItemId || !countSelect) return 0;
    const n = parseInt(countSelect.value, 10);
    return Number.isFinite(n) && n > 0 ? n : 0;
  }

  function showMessage(html) {
    quizArea.textContent = '';
    const p = document.createElement('p');
    p.className = 'empty-msg';
    p.innerHTML = html;        // 文言はこのファイル内の固定文字列のみ
    quizArea.appendChild(p);
    resultEl.classList.add('hidden');
  }

  function buildQuiz(data) {
    let filtered;
    if (urlItemId) {
      filtered = data.filter(d => d.id === urlItemId);
    } else {
      // 種別 → カテゴリの順に絞る
      filtered = (typeSelect && typeSelect.value !== 'all')
        ? byType(data, typeSelect.value)
        : data;
      const cat = categorySelect.value;
      if (cat !== 'all') filtered = filtered.filter(d => d.category === cat);
    }

    let questions = [];
    filtered.forEach(item => {
      (item.quiz || []).forEach((q, idx) => {
        questions.push({ ...q, qid: qidOf(item, q, idx), itemId: item.id, itemName: item.name });
      });
    });

    // 苦手モード：資器材ではなく「問題」単位で絞る。
    // 資器材単位だと、7問中1問だけ落としていても平均85%で苦手に入らず、
    // その1問が永久に出てこない。
    if (weakMode) {
      questions = questions.filter(q => isWeakQid(q.qid));
      if (questions.length === 0) {
        showMessage('苦手問題はまだありません。<br>問題を解いてから確認してください。');
        return;
      }
    }

    if (questions.length === 0) {
      showMessage('この条件の問題はまだありません。');
      return;
    }

    // 復習期限が来たもの → 未回答 → それ以外 の順に並べ、頭から出題数ぶん取る
    questions = sortForStudy(questions);
    const limit = sessionLimit();
    const totalAvailable = questions.length;
    if (limit && questions.length > limit) questions = questions.slice(0, limit);

    quizArea.textContent = '';
    resultEl.classList.add('hidden');

    // 絞り込んだときは母数と並べ方を明示する。
    // showQuestion() が quizArea を毎回空にするので、外側に置く。
    const oldNote = document.querySelector('.quiz-scope-note');
    if (oldNote) oldNote.remove();
    if (limit && totalAvailable > limit) {
      const note = document.createElement('p');
      note.className = 'quiz-scope-note';
      note.textContent =
        `対象 ${totalAvailable}問 から ${limit}問。復習期限が来た問題と未回答を先に出します。`;
      quizArea.before(note);
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

initQuiz();
