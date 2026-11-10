(() => {
  'use strict';
  if (!sessionStorage.getItem('codeexam_token')) { window.location.replace('/ui/login'); return; }
  document.querySelector('[data-nav="faculty"]')?.classList.add('active');
  const $ = id => document.getElementById(id);
  let data = [];
  function render(filter = '') {
    const subset = data.filter(pair => String(pair.a).includes(filter) || String(pair.b).includes(filter));
    const table = $('pairs'); table.replaceChildren();
    if (!subset.length) {
      const tr = document.createElement('tr'), td = document.createElement('td');
      td.colSpan = 4; td.className = 'empty-row';
      td.textContent = data.length ? 'No pairs match your search.' : 'No similarity pairs have been returned yet.';
      tr.appendChild(td); table.appendChild(tr); return;
    }
    subset.forEach((pair, index) => {
      const tr = document.createElement('tr');
      function cell(value, cls = '') { const td = document.createElement('td'); td.textContent = value; td.className = cls; tr.appendChild(td); return td; }
      cell(String(index + 1).padStart(2, '0'), 'muted mono');
      cell('#' + pair.a, 'mono'); cell('#' + pair.b, 'mono');
      const scoreCell = cell((Math.max(0, Math.min(1, Number(pair.score))) * 100).toFixed(1) + '%', 'score-cell');
      const bar = document.createElement('span'); bar.className = 'score-bar' + (Number(pair.score) >= .8 ? ' high' : '');
      const fill = document.createElement('span'); fill.style.width = Math.max(0, Math.min(100, Number(pair.score) * 100)) + '%'; bar.appendChild(fill); scoreCell.appendChild(bar);
      table.appendChild(tr);
    });
  }
  $('pair-search').addEventListener('input', e => render(e.target.value.trim()));
  (async () => {
    try {
      const response = await window.CodeExam.json('/similarity/' + window.CODEEXAM_SIMILARITY_PROBLEM);
      if (!Array.isArray(response)) throw new Error('Similarity API returned an unexpected response.');
      data = response.filter(p => p && Number.isFinite(Number(p.score)) && p.a !== undefined && p.b !== undefined)
        .sort((a, b) => Number(b.score) - Number(a.score));
      $('total-pairs').textContent = data.length.toString();
      $('max-score').textContent = data.length ? (Math.max(...data.map(p => Number(p.score))) * 100).toFixed(1) + '%' : '—';
      $('report-status').textContent = 'Ready'; render();
    } catch (error) {
      $('report-status').textContent = 'Unavailable';
      $('page-alert').classList.add('visible');
      $('page-alert').textContent = error.message + ' The faculty UI is ready, but the similarity module must be integrated by Trisha.';
      $('pairs').replaceChildren(); const tr = document.createElement('tr'), td = document.createElement('td');
      td.colSpan = 4; td.className = 'empty-row'; td.textContent = 'No live report available.'; tr.appendChild(td); $('pairs').appendChild(tr);
    }
  })();
})();
