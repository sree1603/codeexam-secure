(() => {
  'use strict';
  const problem = window.CODEEXAM_PROBLEM;
  const source = document.getElementById('source');
  const lang = document.getElementById('lang');
  const lines = document.getElementById('line-numbers');
  const message = document.getElementById('message');
  const submit = document.getElementById('submit-btn');
  const form = document.getElementById('code-form');
  const save = document.getElementById('save-status');
  const cursor = document.getElementById('cursor-pos');
  const codeEditor = document.getElementById('code-editor');
  const keyBase = `codeexam_draft_${problem.id}_`;
  const templates = {
    python: problem.demo ? 'import sys\n\na, b = map(int, sys.stdin.read().split())\nprint(a + b)\n' : '# Write your Python solution here\nimport sys\n\n',
    cpp: problem.demo ? '#include <iostream>\nusing namespace std;\n\nint main() {\n    long long a, b;\n    cin >> a >> b;\n    cout << a + b << "\\n";\n    return 0;\n}\n' : '#include <iostream>\nusing namespace std;\n\nint main() {\n    // Write your solution here\n    return 0;\n}\n',
  };
  let currentLanguage = 'python';
  let autosaveTimer;
  let inflightKey = null;
  let inflightBody = null;
  let fontSize = 13;
  try { lang.value = sessionStorage.getItem('codeexam_language') || 'python'; } catch (_) {}
  currentLanguage = lang.value;
  try { fontSize = Math.max(11, Math.min(19, Number(localStorage.getItem('codeexam_font_size') || 13))); } catch (_) {}
  function loadDraft(language) {
    try { return localStorage.getItem(keyBase + language) ?? templates[language]; }
    catch (_) { return templates[language]; }
  }
  function storeDraft() {
    try { localStorage.setItem(keyBase + currentLanguage, source.value); save.textContent = 'Saved locally'; }
    catch (_) { save.textContent = 'Local storage unavailable'; }
    document.getElementById('unsaved-dot').classList.remove('visible');
  }
  function redraw() {
    const count = source.value.split('\n').length;
    lines.textContent = Array.from({length:count}, (_, i) => String(i + 1)).join('\n');
    const text = source.value.slice(0, source.selectionStart);
    const row = text.split('\n');
    cursor.textContent = `Ln ${row.length}, Col ${row[row.length - 1].length + 1}`;
  }
  function setSize(n) {
    fontSize = Math.max(11, Math.min(19, n));
    source.style.fontSize = fontSize + 'px';
    lines.style.fontSize = fontSize + 'px';
    document.getElementById('font-label').textContent = fontSize;
    try { localStorage.setItem('codeexam_font_size', String(fontSize)); } catch (_) {}
  }
  function resetIdempotency() { inflightKey = null; inflightBody = null; }
  function setLanguage(next) {
    clearTimeout(autosaveTimer);
    storeDraft(); resetIdempotency();
    currentLanguage = next;
    source.value = loadDraft(next);
    document.getElementById('file-name').textContent = next === 'python' ? 'solution.py' : 'solution.cpp';
    try { sessionStorage.setItem('codeexam_language', next); } catch (_) {}
    source.scrollTop = 0; lines.scrollTop = 0; redraw();
  }
  source.value = loadDraft(currentLanguage);
  document.getElementById('file-name').textContent = currentLanguage === 'python' ? 'solution.py' : 'solution.cpp';
  setSize(fontSize); redraw();
  try { sessionStorage.setItem('codeexam_last_problem', String(problem.id)); } catch (_) {}
  if (!sessionStorage.getItem('codeexam_token')) window.location.replace('/ui/login');
  document.querySelector('[data-nav="workspace"]')?.classList.add('active');
  lang.addEventListener('change', () => setLanguage(lang.value));
  source.addEventListener('input', () => {
    message.textContent = ''; resetIdempotency();
    save.textContent = 'Saving…'; document.getElementById('unsaved-dot').classList.add('visible');
    redraw(); clearTimeout(autosaveTimer); autosaveTimer = setTimeout(storeDraft, 280);
  });
  source.addEventListener('scroll', () => { lines.scrollTop = source.scrollTop; });
  ['click', 'keyup', 'select'].forEach(e => source.addEventListener(e, redraw));
  source.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); form.requestSubmit(); return; }
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = source.selectionStart, end = source.selectionEnd;
      source.setRangeText('    ', start, end, 'end');
      source.dispatchEvent(new Event('input', {bubbles:true}));
    }
  });
  document.getElementById('font-down').addEventListener('click', () => setSize(fontSize - 1));
  document.getElementById('font-up').addEventListener('click', () => setSize(fontSize + 1));
  document.querySelectorAll('[data-tab]').forEach(btn => btn.addEventListener('click', () => {
    const next = btn.dataset.tab;
    document.querySelectorAll('[data-tab]').forEach(tab => {
      const active = tab.dataset.tab === next;
      tab.classList.toggle('active', active); tab.setAttribute('aria-selected', String(active));
      document.getElementById(tab.dataset.tab + '-panel').hidden = !active;
    });
  }));
  document.querySelectorAll('[data-show-tab]').forEach(btn => btn.addEventListener('click', () => {
    document.querySelector('[data-tab="' + btn.dataset.showTab + '"]')?.click();
  }));
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (!window.CodeExam.ensureLogin()) return;
    if (!source.value.trim()) { message.textContent = 'Please write a solution before submitting.'; source.focus(); return; }
    storeDraft();
    const body = JSON.stringify({problem_id:problem.id, language:currentLanguage, source:source.value});
    if (body !== inflightBody) { inflightBody = body; inflightKey = crypto.randomUUID(); }
    submit.disabled = true; submit.textContent = 'Submitting…'; message.textContent = '';
    try {
      const result = await window.CodeExam.json('/submissions', {method:'POST', headers:{'Content-Type':'application/json','Idempotency-Key':inflightKey},body});
      window.location.assign('/ui/submission/' + encodeURIComponent(result.submission_id));
    } catch (error) {
      message.textContent = error.message + ' Retry uses the same submission key.';
      submit.disabled = false; submit.innerHTML = '<span>Submit solution</span><span aria-hidden="true">↗</span>';
    }
  });
})();
