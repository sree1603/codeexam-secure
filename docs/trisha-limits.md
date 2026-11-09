# Honest limits of Trisha's parts (one page)

## Tamper-evident log (`log/`)
- **Deleted newest lines are not detected.** A plain hash chain has nothing after the last line to point back to it. The final project fixes this with signed checkpoints (a signature over the latest hash, stored outside the database).
- **Someone who can edit the database can rewrite the whole chain.** If an attacker edits a row and then recomputes every later hash, the chain looks valid. The chain proves *edits that were not re-hashed*; real protection also needs the latest hash to be stored somewhere else.
- **Verification is only run on request** (`GET /log/verify`). It is not a live alarm.
- **Writes use the same SQLite file as the rest of the app.** Two writers at once are handled by retrying, but a very busy system would need a proper database.

## Copy detector (`triage/`)
- **Python only** in the prototype. C++ submissions are skipped.
- **It can be fooled by rewriting**: reordering independent statements, changing a `for` loop into a `while` loop, or adding useless lines lowers the score.
- **It can accuse honest students.** Two correct answers to a very small problem look alike. A high score is a reason to look, never proof of copying.
- **Broken code** (syntax errors) gets no tokens and is never flagged.
- Comparing every pair is slow for large classes (the number of pairs grows with the square of the number of students).

## Test data (`corpus/`)
- Only 3 small problems and 5 tests each, so a program that passes is not proven correct.
- The 30 sample programs were written by the team, so they are more alike than a real class would be.

## Comparison runners and attacks (`baselines/`, `attacks/network`, `attacks/files`)
- The Docker baseline uses Docker's normal settings plus one memory limit only; a hardened Docker setup would stop more attacks. We report the result honestly either way.
- The attack programs are examples, not a complete list of attacks.
