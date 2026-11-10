(() => {
  'use strict';
  const id = window.CODEEXAM_SUBMISSION_ID;
  const $ = name => document.getElementById(name);
  if (!sessionStorage.getItem('codeexam_token')) { window.location.replace('/ui/login'); return; }
  const back = '/ui/problem/' + encodeURIComponent(sessionStorage.getItem('codeexam_last_problem') || '1');
  $('back-link').href = back; $('back-btn').href = back;
  document.querySelector('[data-nav="workspace"]')?.classList.add('active');
  let attempts = 0;
  async function poll() {
    try {
      const data = await window.CodeExam.json('/submissions/' + id);
      attempts = 0;
      $('page-alert').classList.remove('visible');
      const done = data.status === 'done';
      $('status').textContent = window.CodeExam.label(data.status);
      const verdict = done && data.verdict ? window.CodeExam.label(data.verdict) : 'Pending review';
      $('verdict').textContent = verdict;
      $('verdict-caption').textContent = done ? 'Final grading result' : 'Awaiting the grading worker';
      $('status-orbit').textContent = done ? (data.verdict === 'accepted' ? '✓' : '!') : '⌛';
      $('status-orbit').classList.toggle('active', !done);
      $('test-count').textContent = String(data.tests?.length ?? 0);
      $('test-badge').textContent = done ? 'COMPLETE' : 'LIVE STATUS';
      $('progress').classList.toggle('is-done', done);
      $('banner-title').textContent = done ? 'Grading is complete.' : data.status === 'running' ? 'Your code is being evaluated.' : 'Your solution is in the grading queue.';
      $('banner-message').textContent = done ? 'The verdict and all permitted visible-test details are shown below.' : 'This page refreshes automatically every 2 seconds.';
      $('result-banner').classList.toggle('warning', done && data.verdict !== 'accepted');
      const table = $('tests'); table.replaceChildren();
      if (!data.tests?.length) {
        const row = document.createElement('tr'), cell = document.createElement('td');
        cell.colSpan = 3; cell.className = 'empty-row';
        cell.textContent = done ? 'No visible-test results were returned.' : 'Waiting for test results…';
        row.appendChild(cell); table.appendChild(row);
      } else {
        data.tests.forEach((test, index) => {
          const tr = document.createElement('tr');
          const name = document.createElement('td'); name.textContent = 'Test ' + String(index + 1).padStart(2, '0');
          const result = document.createElement('td'), badge = document.createElement('span');
          badge.className = 'badge ' + (test.verdict === 'accepted' ? 'green' : 'red');
          badge.textContent = window.CodeExam.label(test.verdict); result.appendChild(badge);
          const visibility = document.createElement('td'); visibility.textContent = 'Visible';
          tr.append(name, result, visibility); table.appendChild(tr);
        });
      }
      if (!done) setTimeout(poll, 2000);
    } catch (error) {
      attempts++;
      $('page-alert').textContent = error.message + (attempts < 4 ? ' Retrying…' : ' Reload this page after checking your connection.');
      $('page-alert').classList.add('visible');
      if (attempts < 4) setTimeout(poll, Math.min(2000 * attempts, 6000));
    }
  }
  poll();
})();
