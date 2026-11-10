# Demo script (about 5 minutes)

Owner: Trisha. Everyone reviews. Everything runs locally in WSL, no internet needed.

## Before the demo (do this 10 minutes early)

Open three Ubuntu windows in `~/codeexam-secure` and run `source .venv/bin/activate` in each.

1. `git checkout main && git pull`
2. `rm -f app.db`
3. `python scripts/seed_data.py`
4. `bash scripts/make_canary.sh`
5. Window 1: `make run`   Window 2: `make worker`
6. Open the browser at `http://127.0.0.1:8000/ui/login` and log in as `student1`.
7. Keep the backup video open in another window.
8. Window 3 is for the log and similarity steps (steps 5 and 6 below).

Before step 5, submit 3 programs (one accepted, one wrong, one infinite loop) so the log has at least 3 lines.

## During the demo

| Step | Who speaks | What to do | What the audience sees |
|---|---|---|---|
| 1 | Varshita | Say one sentence: exams run untrusted code, so the grader must be protected. | Nothing to run. |
| 2 | Hanson | Submit a correct program in the browser. | Verdict `accepted`. |
| 3 | Hanson | Submit `while True: pass`. | Verdict `time_limit`; the website keeps working. |
| 4 | Varshita | Open `docs/attack-table.md` (or run `make attacks`). | The naive runner fails attacks; ours contains them. |
| 5 | Trisha | Say: "Every verdict is written to a log; each line holds a fingerprint of the line before it." Run `python -m log.verify` (or open `/log/verify`): `ok: true`. Then run `sqlite3 app.db "UPDATE log_entries SET payload = 'x' WHERE seq = 2;"` and verify again. | `ok: false, first_bad_seq: 2`: the verifier names the edited row. |
| 6 | Trisha | Open `/ui/similarity/1` (or run `python -m triage.demo`). | The planted copy is ranked first. Read out the sentence on the page: "A high score is a reason to look, not proof of copying." |
| 7 | Varshita | State the honest limits (see `docs/known-weaknesses.md` and `docs/trisha-limits.md`). | What is not done: cgroups, real exam scale, deleted newest log lines. |

Steps 5 and 6 have a stand-alone backup that needs no server: `python -m log.demo_tamper` and `python -m triage.demo`.

## If something fails

Stay calm. Say what you expected to see, then switch to the recorded backup video. Do not debug live.
After the demo write the problem in `docs/evidence/demo-notes.md`.

## Questions we should be ready for

- *Why can't a student just edit the log?* Each line contains the hash of the previous line, so one change breaks every later link and the verifier names the first bad line.
- *What can the log not catch?* Deleting the newest lines at the end. The final project adds signed checkpoints.
- *Does a high similarity score prove copying?* No. Two honest answers to a tiny problem can look alike, so it is a reason to look, never proof.
