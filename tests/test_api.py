"""API + worker integration tests with a fixed fake runner; never execute hostile code."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from sqlalchemy import select

from app import db
from app.models import Result, Submission, Test as DBTest, utc_now
from judge import worker


def auth_header(token):
    return {"Authorization": "Bearer " + token}


def fake_runner(request):
    # Simulates Varshita's RESPONSE contract, NOT a secure sandbox.
    correct = {"1": "5\n", "2": "30\n"}
    return {"submission_id": request["submission_id"], "compile": {"ok": True, "message": ""},
            "results": [{"id": t["id"], "stdout": correct[t["id"]], "cpu_ms": 15,
                         "wall_ms": 20, "peak_kb": 9000,
                         "exit_code": 0, "violation": None} for t in request["tests"]]}


def timed_out_runner(request):
    response = fake_runner(request)
    for item in response["results"]:
        item["violation"] = "time_limit"
    return response


def test_health_login_and_pages(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.post("/login", json={"username": "student1", "password": "wrong"}).status_code == 401
    for path in ("/ui/login", "/ui/problem/1", "/ui/submission/1", "/ui/similarity/1"):
        assert client.get(path).status_code == 200
    assert "A high score is a reason to look, not proof of copying." in client.get("/ui/similarity/1").text


def test_requires_token_and_idempotency(client, token_for, submit_as):
    assert client.post("/submissions", json={"problem_id": 1, "language": "python", "source": "x"}).status_code == 401
    first = submit_as()
    assert first.status_code == 202
    second = submit_as()
    assert second.status_code == 202
    assert first.json() == second.json()
    assert submit_as(source="different").status_code == 409
    with db.SessionLocal() as session:
        assert len(session.scalars(select(Submission)).all()) == 1


def test_deadline_and_unknown_problem(client, token_for, monkeypatch):
    headers = {**auth_header(token_for("student1", "pass1")), "Idempotency-Key": "deadline"}
    payload = {"problem_id": 1, "language": "python", "source": "print(1)"}
    monkeypatch.setenv("EXAM_ENDS_AT", "2020-01-01T00:00:00Z")
    assert client.post("/submissions", json=payload, headers=headers).status_code == 403
    monkeypatch.delenv("EXAM_ENDS_AT")
    assert client.post("/submissions", json={**payload, "problem_id": 999}, headers=headers).status_code == 404
    assert client.post("/submissions", json=payload, headers=headers).status_code == 202
    monkeypatch.setenv("EXAM_ENDS_AT", "2020-01-01T00:00:00Z")
    assert client.post("/submissions", json=payload, headers=headers).status_code == 202


def test_private_results_and_hidden_tests(client, token_for, submit_as):
    submission_id = submit_as().json()["submission_id"]
    assert worker.process_one("worker-private", runner=fake_runner) == submission_id
    student = token_for("student1", "pass1")
    other_student = token_for("student2", "pass2")
    faculty = token_for("teacher1", "pass3")
    result = client.get(f"/submissions/{submission_id}", headers=auth_header(student))
    assert result.status_code == 200
    assert result.json() == {"status": "done", "verdict": "accepted",
                             "tests": [{"id": 1, "verdict": "accepted"}]}
    assert client.get(f"/submissions/{submission_id}", headers=auth_header(other_student)).status_code == 404
    teacher_result = client.get(f"/submissions/{submission_id}", headers=auth_header(faculty)).json()
    assert len(teacher_result["tests"]) == 2
    assert "expected_stdout" not in str(result.json())
    assert client.get("/log/verify", headers=auth_header(student)).status_code == 403
    assert client.get("/similarity/1", headers=auth_header(student)).status_code == 403
    # If Trisha hasn't added these modules yet, do NOT make up verification results.
    assert client.get("/log/verify", headers=auth_header(faculty)).json() == {"ok": True, "first_bad_seq": None}
    assert client.get("/similarity/1", headers=auth_header(faculty)).status_code == 200


def test_two_workers_only_claim_one_submission(client, submit_as):
    submission_id = submit_as().json()["submission_id"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(worker.claim_next, "unique-A")
        b = pool.submit(worker.claim_next, "unique-B")
    assert sorted([a.result(), b.result()], key=lambda x: x is None) == [submission_id, None]
    with db.SessionLocal() as session:
        assert session.get(Submission, submission_id).status == "running"


def test_end_to_end_accepted_and_timeout(client, token_for, submit_as):
    accepted_id = submit_as(key="correct", source="print(5)").json()["submission_id"]
    timeout_id = submit_as(key="loop", source="while True: pass").json()["submission_id"]
    worker.process_one("worker-ok", runner=fake_runner)
    worker.process_one("worker-timeout", runner=timed_out_runner)
    headers = auth_header(token_for("student1", "pass1"))
    assert client.get(f"/submissions/{accepted_id}", headers=headers).json()["verdict"] == "accepted"
    assert client.get(f"/submissions/{timeout_id}", headers=headers).json()["verdict"] == "time_limit"
    with db.SessionLocal() as session:
        assert len(session.scalars(select(Result)).all()) == 4


def test_stale_job_is_requeued_and_reclaimed(client, submit_as):
    submission_id = submit_as().json()["submission_id"]
    assert worker.claim_next("died-worker") == submission_id
    with db.SessionLocal.begin() as session:
        sub = session.get(Submission, submission_id)
        sub.claimed_at = utc_now() - timedelta(minutes=3)
    assert worker.process_one("restarted-worker", runner=fake_runner) == submission_id
    with db.SessionLocal() as session:
        assert session.get(Submission, submission_id).status == "done"
        assert len(session.scalars(select(Result)).all()) == 2


def test_runner_fails_once_retries_then_internal_error(client, submit_as):
    submission_id = submit_as().json()["submission_id"]

    def unavailable(request):
        raise RuntimeError("secure runner not yet installed")

    worker.process_one("bad-first", runner=unavailable)
    with db.SessionLocal() as session:
        sub = session.get(Submission, submission_id)
        assert sub.status == "queued" and sub.retry_count == 1
    worker.process_one("bad-second", runner=unavailable)
    with db.SessionLocal() as session:
        sub = session.get(Submission, submission_id)
        assert sub.status == "done" and sub.verdict == "internal_error"


def test_compile_error_has_per_test_results(client, submit_as):
    submission_id = submit_as(key="compile", source="broken C++").json()["submission_id"]

    def compilation_error(request):
        return {"submission_id": request["submission_id"],
                "compile": {"ok": False, "message": "syntax error"}, "results": []}

    worker.process_one("compile-worker", runner=compilation_error)
    with db.SessionLocal() as session:
        assert session.get(Submission, submission_id).verdict == "compile_error"
        assert all(r.verdict == "compile_error" for r in session.scalars(select(Result)).all())


def test_load_problem_file_and_replace_tests(client, tmp_path):
    import json
    from app.problems import load_problem
    folder = tmp_path / "sample"
    folder.mkdir()
    problem = {"id": 7, "title": "Seven", "limits": {"cpu_ms": 2000,
               "wall_ms": 5000, "memory_mb": 256, "processes": 8, "output_kb": 1024},
               "tests": [{"id": 70, "stdin": "1\n", "expected_stdout": "1\n", "hidden": False}]}
    (folder / "problem.json").write_text(json.dumps(problem), encoding="utf-8")
    assert load_problem(folder) == 7
    problem["tests"][0]["expected_stdout"] = "2\n"
    (folder / "problem.json").write_text(json.dumps(problem), encoding="utf-8")
    assert load_problem(folder) == 7
    with db.SessionLocal() as session:
        rows = session.scalars(select(DBTest).where(DBTest.problem_id == 7)).all()
        assert len(rows) == 1 and rows[0].expected_stdout == "2\n"


def test_worker_calls_runner_contract_without_executing_user_code(client, submit_as, monkeypatch):
    import json
    from pathlib import Path
    from types import SimpleNamespace
    seen = []

    def fake_subprocess(command, cwd, capture_output, text, timeout, check):
        assert command[:2] == ["sudo", "-n"]
        assert command[-3:-1] == ["-m", "runner.run_cli"]
        request = json.loads(Path(command[-1]).read_text())
        seen.append((request, command[-1]))
        return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps(fake_runner(request)))

    monkeypatch.setattr(worker.subprocess, "run", fake_subprocess)
    submission_id = submit_as(key="runner-contract").json()["submission_id"]
    assert worker.process_one("contract-check-worker") == submission_id
    assert len(seen) == 1
    assert set(seen[0][0]) == {"submission_id", "language", "source", "limits", "tests"}
    assert len(seen[0][0]["tests"]) == 2
    assert not Path(seen[0][1]).exists()  # runner request temp file deleted


def test_trisha_log_hook_payload_when_installed(client, submit_as, monkeypatch):
    import sys
    from types import ModuleType
    payloads = []
    package = ModuleType("log")
    package.__path__ = []
    chain = ModuleType("log.chain")
    chain.append_entry = payloads.append
    monkeypatch.setitem(sys.modules, "log", package)
    monkeypatch.setitem(sys.modules, "log.chain", chain)

    submission_id = submit_as(key="logger").json()["submission_id"]
    worker.process_one("logger-worker", runner=fake_runner)
    assert len(payloads) == 1
    assert payloads[0]["submission_id"] == submission_id
    assert payloads[0]["verdict"] == "accepted"
    assert payloads[0]["time"].endswith("Z")

def test_login_returns_role(client):
    student = client.post("/login", json={"username": "student1", "password": "pass1"}).json()
    faculty = client.post("/login", json={"username": "teacher1", "password": "pass3"}).json()
    assert student["role"] == "student" and student["token"]
    assert faculty["role"] == "faculty" and faculty["token"]
