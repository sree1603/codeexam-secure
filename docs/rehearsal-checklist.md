# Rehearsal checklist (Card I, Varshita)

Use this together with `docs/demo-script.md` (Trisha writes it).

## Before each rehearsal

- [ ] `git checkout main && git pull`
- [ ] `bash scripts/check_env.sh` shows PASS
- [ ] `rm -f app.db`, `python scripts/seed_data.py`, `bash scripts/make_canary.sh`
- [ ] Terminal 1: `make run`.  Terminal 2: `make worker`.  Browser open on the login page
- [ ] A timer is running (the whole demo must fit in about 5 minutes)

## Rehearsal 1 and 2

- [ ] Every step of the demo script worked without asking a question
- [ ] Time taken: ______ (rehearsal 1) ______ (rehearsal 2)
- [ ] Things that went wrong and the fix: ______________________

## Backup video

- [ ] Record the full demo once (Windows: Win + G opens Game Bar, then Record)
- [ ] Save the file, upload it somewhere the team can open, and put the link in `docs/evidence/README.md`

## Evidence pack (`docs/evidence/`)

- [ ] `bash scripts/collect_evidence.sh` ran and the folder was committed
- [ ] Screenshot of one attack being contained (for example `cpu1.py` ending with `time_limit`)
- [ ] `docs/attack-table.md` has the honest paragraph filled in
- [ ] Known weaknesses list (`docs/known-weaknesses.md`) read by all three of us
