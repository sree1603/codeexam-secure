hanson-fixes(() => {
  'use strict';
  const root = document.documentElement;
  let theme;
  try { theme = localStorage.getItem('codeexam_theme') || 'dark'; } catch (_) { theme = 'dark'; }
  root.dataset.theme = theme === 'light' ? 'light' : 'dark';
  document.querySelectorAll('.theme-toggle').forEach(btn => btn.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('codeexam_theme', next); } catch (_) {}
  }));
  document.getElementById('logout')?.addEventListener('click', () => {
    sessionStorage.removeItem('codeexam_token');
    sessionStorage.removeItem('codeexam_role');
    window.location.replace('/ui/login');
  });
  document.querySelectorAll('[data-copy]').forEach(btn => btn.addEventListener('click', async () => {
    const target = document.getElementById(btn.dataset.copy);
    if (!target) return;
    try { await navigator.clipboard.writeText(target.textContent); window.CodeExam.toast('Copied to clipboard'); }
    catch (_) { window.CodeExam.toast('Clipboard unavailable. Select the text to copy.', true); }
  }));
  window.CodeExam = {
    token: () => sessionStorage.getItem('codeexam_token'),
    ensureLogin() {
      if (!this.token()) { window.location.replace('/ui/login'); return false; }
      return true;
    },
    toast(message, error = false) {
      const el = document.getElementById('toast');
      if (!el) return;
      el.textContent = message;
      el.classList.toggle('is-error', !!error);
      el.classList.add('visible');
      clearTimeout(el._timeout);
      el._timeout = setTimeout(() => el.classList.remove('visible'), 3500);
    },
    async json(url, options = {}) {
      const r = await fetch(url, {
        ...options,
        headers: { ...(options.headers || {}), 'Authorization': 'Bearer ' + this.token() },
      });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        const detail = body.detail;
        if (r.status === 401) {
          sessionStorage.removeItem('codeexam_token');
          throw new Error('Your session expired. Please sign in again.');
        }
        throw new Error(typeof detail === 'string' ? detail : 'Request failed (HTTP ' + r.status + ')');
      }
      return body;
    },
    label(value) {
      return String(value || 'pending').replace(/_/g, ' ').replace(/\b\w/g, x => x.toUpperCase());
    },
  };
})();
