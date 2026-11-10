"""Student and faculty browser views. Backend API remains the team's agreed contract."""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Problem, Test

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/ui/login")


@router.get("/ui/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.get("/ui/problem/{problem_id}", response_class=HTMLResponse)
def problem_page(request: Request, problem_id: int):
    with SessionLocal() as session:
        problem = session.get(Problem, problem_id)
        if problem is None:
            raise HTTPException(status_code=404, detail="Problem not found")
        # Visible samples only. Hidden inputs, outputs and even IDs NEVER reach HTML.
        samples = session.scalars(
            select(Test).where(Test.problem_id == problem_id, Test.hidden.is_(False))
            .order_by(Test.id)
        ).all()
        available = session.scalars(select(Problem).order_by(Problem.id)).all()
        limits = json.loads(problem.limits_json)
        return templates.TemplateResponse(
            request=request, name="problem.html", context={
                "problem_id": problem_id,
                "title": problem.title,
                "is_demo_sum": problem.title == "Sum of two numbers (demo)",
                "samples": [{"input": item.stdin, "output": item.expected_stdout}
                            for item in samples],
                "problems": [{"id": item.id, "title": item.title} for item in available],
                "limits": limits,
            },
        )


@router.get("/ui/submission/{submission_id}", response_class=HTMLResponse)
def submission_page(request: Request, submission_id: int):
    return templates.TemplateResponse(request=request, name="submission.html",
                                      context={"submission_id": submission_id})


@router.get("/ui/similarity/{problem_id}", response_class=HTMLResponse)
def similarity_page(request: Request, problem_id: int):
    return templates.TemplateResponse(request=request, name="similarity.html",
                                      context={"problem_id": problem_id})
