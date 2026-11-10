"""Single-job claiming, runner invocation, verdicts and stale-worker recovery."""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import timedelta
from pathlib import Path

from sqlalchemy import delete, select, text

from app.db import SessionLocal, create_tables
from app.models import Problem, Result, Submission, Test, utc_now
from judge.verdict import decide_test, overall_verdict

REPO_ROOT = Path(__file__).resolve().parents[1]
# Each worker instance uses one unique claim ID, never a shared constant.
WORKER_ID = f"worker-{uuid.uuid4().hex}"
STALE_AFTER_SECONDS = 120


def reclaim_stale_jobs():
    cutoff = utc_now() - timedelta(seconds=STALE_AFTER_SECONDS)
    with SessionLocal.begin() as session:
        session.execute(text("""
            UPDATE submissions SET status = 'queued', claimed_by = NULL, claimed_at = NULL
            WHERE status = 'running' AND claimed_at < :cutoff
        """), {"cutoff": cutoff})


def claim_next(worker_id: str = WORKER_ID) -> int | None:
    # Atomic single-statement claim, as specified in Hanson's Task 7.
    with SessionLocal.begin() as session:
        changed = session.execute(text("""
            UPDATE submissions SET status = 'running', claimed_by = :worker, claimed_at = :now
            WHERE id = (SELECT id FROM submissions WHERE status = 'queued' ORDER BY id LIMIT 1)
              AND status = 'queued'
        """), {"worker": worker_id, "now": utc_now()})
        if changed.rowcount != 1:
            return None
        submission_id = session.scalar(select(Submission.id)
                                        .where(Submission.claimed_by == worker_id,
                                               Submission.status == "running")
                                        .order_by(Submission.id.desc()))
        return submission_id


def build_request(submission_id: int) -> tuple[dict, list[dict]]:
    with SessionLocal() as session:
        item = session.get(Submission, submission_id)
        if item is None:
            raise ValueError("Missing submission")
        problem = session.get(Problem, item.problem_id)
        if problem is None:
            raise ValueError("Missing problem")
        tests = session.scalars(select(Test).where(Test.problem_id == problem.id)
                                .order_by(Test.id)).all()
        if not tests:
            raise ValueError("Problem has no tests")
        request = {
            "submission_id": f"s-{item.id:04d}",
            "language": item.language,
            "source": item.source,
            "limits": json.loads(problem.limits_json),
            "tests": [{"id": str(t.id), "stdin": t.stdin} for t in tests],
        }
        # Keep plain records outside the session, avoiding detached entity surprises.
        test_data = [{"id": t.id, "expected": t.expected_stdout} for t in tests]
        return request, test_data


def run_secure_runner(request: dict) -> dict:
    """Only Varshita's locked runner is allowed to execute submitted code."""
    request_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8",
                                         delete=False) as f:
            json.dump(request, f)
            request_file = f.name
        # Sudo is deliberately not used for web app. Restrict privileged execution to a lab WSL.
        command = ["sudo", "-n", str(REPO_ROOT / ".venv/bin/python"),
                   "-m", "runner.run_cli", request_file]
        result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True,
                                text=True, timeout=60, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Runner exited {result.returncode}: {result.stderr[:250]}")
        response = json.loads(result.stdout)
        if response.get("submission_id") != request["submission_id"]:
            raise ValueError("Runner returned a different submission ID")
        if not isinstance(response.get("compile"), dict) or not isinstance(response.get("results"), list):
            raise ValueError("Invalid runner response")
        return response
    finally:
        if request_file is not None:
            try:
                os.unlink(request_file)
            except FileNotFoundError:
                pass


def grade_response(response: dict, tests: list[dict]) -> list[dict]:
    compile_info = response["compile"]
    if not isinstance(compile_info.get("ok"), bool):
        raise ValueError("Runner missing compile.ok")
    results = response["results"]
    if any(entry.get("violation") == "launcher_error" for entry in results):
        raise RuntimeError("Runner could not start the sandbox (launcher_error)")
    if not compile_info["ok"]:
        # C++ compile errors have no per-test runner result.
        return [{"test_id": t["id"], "verdict": "compile_error",
                 "cpu_ms": None, "wall_ms": None, "peak_kb": None} for t in tests]
    lookup = {str(entry["id"]): entry for entry in results}
    if len(lookup) != len(tests) or len(results) != len(tests):
        raise ValueError("Runner result count does not match supplied tests")
    grades = []
    for test in tests:
        result = lookup.get(str(test["id"]))
        if result is None:
            raise ValueError("Missing test result")
        verdict = decide_test(compile_info, result, test["expected"])
        grades.append({"test_id": test["id"], "verdict": verdict,
                       "cpu_ms": result.get("cpu_ms"), "wall_ms": result.get("wall_ms"),
                       "peak_kb": result.get("peak_kb")})
    return grades


def record_log(submission_id: int, verdict: str):
    """Trisha owns this implementation. Never fake an audit entry on integration failure."""
    try:
        from log.chain import append_entry
    except ImportError:
        print("LOG INTEGRATION PENDING: log.chain.append_entry is not available", file=sys.stderr)
        return False
    payload = {"submission_id": submission_id, "verdict": verdict,
               "time": utc_now().isoformat() + "Z"}
    try:
        append_entry(payload)
        return True
    except Exception as exc:
        print(f"LOG INTEGRATION FAILED for submission {submission_id}: {exc}", file=sys.stderr)
        return False


def finalize(submission_id: int, worker_id: str, grades: list[dict]) -> bool:
    verdict = overall_verdict([g["verdict"] for g in grades])
    with SessionLocal.begin() as session:
        item = session.get(Submission, submission_id)
        if item is None or item.status != "running" or item.claimed_by != worker_id:
            return False  # an expired worker may not overwrite a new owner's results
        session.execute(delete(Result).where(Result.submission_id == submission_id))
        for grade in grades:
            session.add(Result(submission_id=submission_id, test_id=grade["test_id"],
                               verdict=grade["verdict"], cpu_ms=grade["cpu_ms"],
                               wall_ms=grade["wall_ms"], peak_kb=grade["peak_kb"]))
        item.status = "done"
        item.verdict = verdict
        item.claimed_by = None
        item.claimed_at = None
    record_log(submission_id, verdict)
    return True


def handle_runner_error(submission_id: int, worker_id: str, error: Exception):
    print(f"Runner error for submission {submission_id}: {error}", file=sys.stderr)
    mark_final = False
    with SessionLocal.begin() as session:
        item = session.get(Submission, submission_id)
        if item is None or item.status != "running" or item.claimed_by != worker_id:
            return
        if item.retry_count < 1:
            item.retry_count += 1
            item.status = "queued"
        else:
            item.status = "done"
            item.verdict = "internal_error"
            mark_final = True
        item.claimed_by = None
        item.claimed_at = None
    if mark_final:
        record_log(submission_id, "internal_error")


def process_one(worker_id: str = WORKER_ID, runner=None) -> int | None:
    """Run one queued job; runner injection exists for tests ONLY, not the deployed worker."""
    reclaim_stale_jobs()
    submission_id = claim_next(worker_id)
    if submission_id is None:
        return None
    try:
        request, tests = build_request(submission_id)
        response = (runner or run_secure_runner)(request)
        grades = grade_response(response, tests)
        finalize(submission_id, worker_id, grades)
    except Exception as exc:
        handle_runner_error(submission_id, worker_id, exc)
    return submission_id


def main():
    parser = argparse.ArgumentParser(description="Secure grading worker (WSL only)")
    parser.add_argument("--once", action="store_true", help="Handle at most one queued submission")
    args = parser.parse_args()
    create_tables()
    print(f"Worker {WORKER_ID} active; submitted code goes ONLY to runner.run_cli", flush=True)
    while True:
        processed = process_one()
        if args.once:
            return
        if processed is None:
            time.sleep(1)


if __name__ == "__main__":
    main()
