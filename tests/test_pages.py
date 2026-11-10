"""Web UI integration checks: ensure no hidden data enters rendered HTML."""
from app.models import Test as ProblemTest
from app import db


def test_login_page_and_local_assets(client):
    login = client.get('/ui/login')
    assert login.status_code == 200
    assert 'Student portal' in login.text
    assert 'Faculty portal' in login.text
    for name in ('/static/css/app.css', '/static/js/login.js', '/static/js/editor.js',
                 '/static/js/submission.js', '/static/js/similarity.js', '/static/js/common.js'):
        response = client.get(name)
        assert response.status_code == 200, name


def test_problem_page_shows_only_visible_tests(client):
    with db.SessionLocal.begin() as session:
        row = session.get(ProblemTest, 2)
        row.stdin = 'HIDDEN_INPUT_DO_NOT_LEAK_1234'
        row.expected_stdout = 'HIDDEN_EXPECTED_DO_NOT_LEAK_5678'
    response = client.get('/ui/problem/1')
    assert response.status_code == 200
    assert '2 3' in response.text
    assert '5' in response.text
    assert 'HIDDEN_INPUT_DO_NOT_LEAK_1234' not in response.text
    assert 'HIDDEN_EXPECTED_DO_NOT_LEAK_5678' not in response.text
    assert 'Code editor' in response.text
    assert 'Submit solution' in response.text


def test_result_and_faculty_pages_render(client):
    for path, text in [('/ui/submission/42', 'Test case breakdown'),
                       ('/ui/similarity/1', 'Similarity review')]:
        response = client.get(path)
        assert response.status_code == 200
        assert text in response.text
        assert '<html' in response.text


def test_problem_not_found(client):
    assert client.get('/ui/problem/987654').status_code == 404
