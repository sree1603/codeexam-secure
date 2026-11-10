"""Load Trisha's problem.json files without modifying her corpus."""
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Problem, Test

REQUIRED_LIMITS = {"cpu_ms", "wall_ms", "memory_mb", "processes", "output_kb"}


def load_problem(folder: str | Path, session: Session | None = None) -> int:
    folder = Path(folder)
    data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
    for name in ("id", "title", "limits", "tests"):
        if name not in data:
            raise ValueError(f"Missing problem.json field: {name}")
    if not REQUIRED_LIMITS.issubset(data["limits"]):
        raise ValueError("Problem limits do not match the runner contract")
    if not data["tests"]:
        raise ValueError("Problem must include at least one test")

    own_session = session is None
    if own_session:
        session = SessionLocal()
    try:
        problem_id = int(data["id"])
        existing = session.get(Problem, problem_id)
        if existing is None:
            session.add(Problem(id=problem_id, title=str(data["title"]),
                                limits_json=json.dumps(data["limits"])))
        else:
            existing.title = str(data["title"])
            existing.limits_json = json.dumps(data["limits"])
        session.flush()
        # "t1" is only a label (every problem uses it), so the database numbers tests itself.
        rows = session.scalars(select(Test).where(Test.problem_id == problem_id)
                               .order_by(Test.id)).all()
        for position, item in enumerate(data["tests"]):
            for name in ("stdin", "expected_stdout", "hidden"):
                if name not in item:
                    raise ValueError(f"Test {position + 1} is missing '{name}'")
            if position < len(rows):
                row = rows[position]
                row.stdin = str(item["stdin"])
                row.expected_stdout = str(item["expected_stdout"])
                row.hidden = bool(item["hidden"])
            else:
                session.add(Test(problem_id=problem_id, stdin=str(item["stdin"]),
                                 expected_stdout=str(item["expected_stdout"]),
                                 hidden=bool(item["hidden"])))
        for extra in rows[len(data["tests"]):]:
            session.delete(extra)
        if own_session:
            session.commit()
        return problem_id
    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()
