"""Isolated SQLite database for Hanson's tests: no attack programs are executed."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app import auth, db
from app.main import app
from app.models import Problem, Test, User


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}",
                                connect_args={"check_same_thread": False, "timeout": 30})
    monkeypatch.setattr(db, "engine", test_engine)
    db.SessionLocal.configure(bind=test_engine)
    auth.TOKENS.clear()
    with TestClient(app) as test_client:
        with db.SessionLocal.begin() as session:
            session.add_all([
                User(username="student1", password_hash=auth.hash_password("pass1"), role="student"),
                User(username="student2", password_hash=auth.hash_password("pass2"), role="student"),
                User(username="teacher1", password_hash=auth.hash_password("pass3"), role="faculty"),
                Problem(id=1, title="Demo sum", limits_json='{"cpu_ms":2000,"wall_ms":5000,"memory_mb":256,"processes":8,"output_kb":1024}'),
                Test(id=1, problem_id=1, stdin="2 3\n", expected_stdout="5\n", hidden=False),
                Test(id=2, problem_id=1, stdin="10 20\n", expected_stdout="30\n", hidden=True),
            ])
        yield test_client
    auth.TOKENS.clear()
    test_engine.dispose()


@pytest.fixture
def token_for(client):
    def get(username: str, password: str) -> str:
        r = client.post("/login", json={"username": username, "password": password})
        assert r.status_code == 200
        return r.json()["token"]
    return get


@pytest.fixture
def submit_as(client, token_for):
    def submit(username="student1", password="pass1", key="request-1", source="print(5)"):
        token = token_for(username, password)
        return client.post("/submissions", headers={"Authorization": f"Bearer {token}",
                                                     "Idempotency-Key": key},
                           json={"problem_id": 1, "language": "python", "source": source})
    return submit
