# CodeExam Secure — API contract (Hanson / Person 2)

All JSON contracts are copied from the team's *Prototype Workflow and Team Guide*. Do not rename endpoints or change fields without a team-approved GitHub issue.

## Login

`POST /login` public endpoint:

Request:
```json
{"username":"student1","password":"student123"}
```
Response `200`:
```json
{"token":"a-session-specific-random-token", "role" : "student"}
`role` is `student` or `faculty`; the UI uses it to choose the landing page and which links to show.
```
A wrong password gives `401`. Tokens are stored in memory and disappear when the server restarts.

## Submit code

`POST /submissions` for students. Headers: `Authorization: Bearer <token>` and `Idempotency-Key: <text>`.

Request:
```json
{"problem_id":1,"language":"python","source":"print(sum(map(int, input().split())))"}
```
Response `202`:
```json
{"submission_id":42,"status":"queued"}
```
The same user/key/request combination returns the original submission (no duplicate grading). Using a key for another user/payload returns `409`. An expired `EXAM_ENDS_AT` causes `403`. `EXAM_ENDS_AT` should use an ISO 8601 timestamp with timezone, such as `2026-11-04T10:00:00+05:30`.

## Read verdict

`GET /submissions/42` with `Authorization: Bearer <token>`:

Response `200` (after grading):
```json
{"status":"done","verdict":"accepted","tests":[{"id":1,"verdict":"accepted"}]}
```
A queued submission has `{"status":"queued","verdict":null,"tests":[]}`. A student sees **only visible-test** verdicts, never hidden-test inputs, expected outputs or other users' code. Another student's submission returns `404`.

## Verify the log (Trisha-owned implementation)

`GET /log/verify` (faculty only):

Response `200` after Trisha integrates `log.verify.verify_log()`:
```json
{"ok":true,"first_bad_seq":null}
```
Without the verifier installed, endpoint returns `503`, **not fake success**.

## Similarity pairs (Trisha-owned implementation)

`GET /similarity/1` (faculty only):

Response `200` after Trisha integrates `triage.report.get_similarity(problem_id)`:
```json
[{"a":42,"b":57,"score":0.91}]
```
Without the report function it returns `503`. Similarity is evidence for human review, not a guilty verdict.

## Additional routes already described by guide

- `GET /health` → `{"status":"ok"}`
- `GET /ui/login`, `GET /ui/problem/{id}`, `GET /ui/submission/{id}`, `GET /ui/similarity/{id}` — browser views (Card G).

## Runner boundary (Varshita-owned)

The worker writes the request JSON file then executes `sudo -n .venv/bin/python -m runner.run_cli <request-file>` inside WSL. The request/response JSON field names come **only** from `contracts/runner.md` and the agreed guide. No unsandboxed code execution fallback is permitted.

**Team integration confirmations needed:** Trisha confirms `append_entry(payload)`, `verify_log()` and `get_similarity(problem_id)` signatures. Varshita confirms the runner contract including `exit_code` and `id` fields, then verifies sudo/namespace compatibility in WSL.
