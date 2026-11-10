(() => {
  'use strict';
  const form = document.getElementById('login-form');
  const student = document.getElementById('student-portal');
  const faculty = document.getElementById('faculty-portal');
  const error = document.getElementById('message');
  const submit = document.getElementById('sign-in');
  let role = 'student';
  function switchPortal(next) {
    role = next;
    for (const [button, selected] of [[student, next === 'student'], [faculty, next === 'faculty']]) {
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-pressed', String(selected));
    }
    error.textContent = '';
  }
  student.addEventListener('click', () => switchPortal('student'));
  faculty.addEventListener('click', () => switchPortal('faculty'));
  document.getElementById('show-password').addEventListener('click', function () {
    const input = document.getElementById('password');
    input.type = input.type === 'password' ? 'text' : 'password';
    this.textContent = input.type === 'password' ? 'SHOW' : 'HIDE';
  });
  form.addEventListener('submit', async event => {
    event.preventDefault(); error.textContent = ''; submit.disabled = true; submit.textContent = 'Signing in…';
    try {
      const response = await fetch('/login', { method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({username:document.getElementById('username').value.trim(), password:document.getElementById('password').value}) });
      const data = await response.json();
      if (!response.ok || !data.token) throw new Error('Incorrect username or password. Please try again.');
      sessionStorage.setItem('codeexam_token', data.token);
      sessionStorage.setItem('codeexam_role', role);
      // Role authorization is still enforced on the API; this selector only chooses the destination.
      window.location.assign(role === 'faculty' ? '/ui/similarity/1' : '/ui/problem/1');
    } catch (e) {
      error.textContent = e.message || 'Unable to sign in. Check your connection.';
      submit.disabled = false; submit.textContent = 'Sign in →';
    }
  });
})();
