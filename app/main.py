"""CodeExam Secure's HTTP API; grading is performed by a separate worker."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, issue_token, require_faculty, verify_password
from app.db import create_tables, get_db
from app.models import Problem, Result, Submission, Test, User
from app import pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="CodeExam Secure", lifespan=lifespan)
app.include_router(pages.router)
# Local, self-hosted UI assets; no CDN required for the exam interface.
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


class LoginRequest(BaseModel):
    username: str
    password: str


class SubmitRequest(BaseModel):
    problem_id: int
    language: str
    source: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_db)):
    user = session.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": issue_token(user)}


def deadline_passed() -> bool:
    value = os.getenv("EXAM_ENDS_AT", "").strip()
    if not value:
        return False
    try:
        cutoff = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid EXAM_ENDS_AT configuration") from exc
    return datetime.now(timezone.utc) >= cutoff


@app.post("/submissions", status_code=status.HTTP_202_ACCEPTED)
def submit(payload: SubmitRequest,
           idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
           user: User = Depends(get_current_user), session: Session = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students may submit code")
    if not idempotency_key or not (1 <= len(idempotency_key) <= 200):
        raise HTTPException(status_code=400, detail="Idempotency-Key header required (max 200 chars)")
    if payload.language not in ("python", "cpp") or not payload.source.strip() or len(payload.source) > 200_000:
        raise HTTPException(status_code=422, detail="Use python/cpp with nonempty source (max 200000 characters)")

    # Retry before the deadline must return its existing submission, even when the exam is now closed.
    old = session.scalar(select(Submission).where(Submission.idempotency_key == idempotency_key))
    if old:
        return duplicate_response(old, user, payload)
    if deadline_passed():
        raise HTTPException(status_code=403, detail="Exam deadline has passed")
    if not session.get(Problem, payload.problem_id):
        raise HTTPException(status_code=404, detail="Problem not found")
    new = Submission(user_id=user.id, problem_id=payload.problem_id,
                     language=payload.language, source=payload.source,
                     idempotency_key=idempotency_key, status="queued")
    session.add(new)
    try:
        session.commit()
        session.refresh(new)
    except IntegrityError:
        # Two concurrent identical requests may race on the UNIQUE key.
        session.rollback()
        old = session.scalar(select(Submission).where(Submission.idempotency_key == idempotency_key))
        if old:
            return duplicate_response(old, user, payload)
        raise
    return {"submission_id": new.id, "status": "queued"}


def duplicate_response(old: Submission, user: User, payload: SubmitRequest) -> dict:
    if (old.user_id != user.id or old.problem_id != payload.problem_id or
            old.language != payload.language or old.source != payload.source):
        raise HTTPException(status_code=409, detail="Idempotency key already used for a different request")
    return {"submission_id": old.id, "status": old.status}


@app.get("/submissions/{submission_id}")
def read_submission(submission_id: int, user: User = Depends(get_current_user),
                    session: Session = Depends(get_db)):
    item = session.get(Submission, submission_id)
    if item is None or (user.role != "faculty" and item.user_id != user.id):
        raise HTTPException(status_code=404, detail="Submission not found")
    # students never see hidden test details (even IDs). Faculty may see per-test verdicts.
    visible = []
    for result in session.scalars(select(Result).where(Result.submission_id == item.id)
                                  .order_by(Result.test_id)):
        test = session.get(Test, result.test_id)
        if test and (user.role == "faculty" or not test.hidden):
            visible.append({"id": test.id, "verdict": result.verdict})
    return {"status": item.status, "verdict": item.verdict, "tests": visible}


@app.get("/log/verify")
def verify_log(user: User = Depends(get_current_user)):
    require_faculty(user)
    try:
        from log.verify import verify_log as verifier
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Trisha's log verifier is not installed") from exc
    # Integrator must agree on the function's actual signature before merging.
    result = verifier()
    if not isinstance(result, dict) or "ok" not in result or "first_bad_seq" not in result:
        raise HTTPException(status_code=503, detail="Log verifier contract not agreed")
    return {"ok": result["ok"], "first_bad_seq": result["first_bad_seq"]}


@app.get("/similarity/{problem_id}")
def similarity(problem_id: int, user: User = Depends(get_current_user)):
    require_faculty(user)
    try:
        from triage.report import get_similarity
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Trisha's similarity report is not installed") from exc
    data = get_similarity(problem_id)
    if not isinstance(data, list):
        raise HTTPException(status_code=503, detail="Similarity report contract not agreed")
    return data
