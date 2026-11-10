"""Idempotent demo users + Trisha's corpus files; run from project root."""
import os
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.auth import hash_password
from app.db import SessionLocal, create_tables
from app.models import Problem, Test, User
from app.problems import load_problem

DEMO_LIMITS = '{"cpu_ms":2000,"wall_ms":5000,"memory_mb":256,"processes":8,"output_kb":1024}'


def seed():
    create_tables()
    with SessionLocal.begin() as session:
        for username, role, env_name, default in (
            ("student1", "student", "DEMO_STUDENT_PASSWORD", "student123"),
            ("teacher1", "faculty", "DEMO_TEACHER_PASSWORD", "teacher123"),
        ):
            if session.scalar(select(User).where(User.username == username)) is None:
                session.add(User(username=username, role=role,
                                 password_hash=hash_password(os.getenv(env_name, default))))
    corpus_root = ROOT / "corpus" / "problems"
    folders = sorted(corpus_root.glob("*/problem.json")) if corpus_root.exists() else []
    if folders:
        for file in folders:
            problem_id = load_problem(file.parent)
            print(f"Loaded problem {problem_id} from {file.parent}")
    else:
        # Non-corpus fallback for initial team integration; does NOT write Trisha's files.
        with SessionLocal.begin() as session:
            if session.get(Problem, 1) is None:
                session.add(Problem(id=1, title="Sum of two numbers (demo)", limits_json=DEMO_LIMITS))
                session.add_all([
                    Test(id=1, problem_id=1, stdin="2 3\n", expected_stdout="5\n", hidden=False),
                    Test(id=2, problem_id=1, stdin="10 20\n", expected_stdout="30\n", hidden=True),
                ])
        print("Seeded demo problem 1; replace with Trisha's corpus when available")
    print("Demo users: student1 / teacher1 (set DEMO_*_PASSWORD before seeding)")
    print("WARNING: Default passwords are ONLY for isolated prototype development")


if __name__ == "__main__":
    seed()
