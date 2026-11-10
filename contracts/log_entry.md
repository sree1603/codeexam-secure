# Log Entry Format

Each log entry contains four fields:

- `seq`: Sequential number starting from 1.
- `payload`: The event details stored as JSON text.
- `prev_hash`: SHA-256 hash of the previous entry.
- `hash`: SHA-256 hash calculated using `seq|payload|prev_hash`.

## Hash Calculation

The hash is calculated as:

    hash = sha256("seq|payload|prev_hash")

For the first entry, `prev_hash` must contain 64 zeros.

## Worked Example

Entry 1:

    seq = 1
    payload = {"event":"test"}
    prev_hash = 0000000000000000000000000000000000000000000000000000000000000000

The string being hashed is:

    1|{"event":"test"}|0000000000000000000000000000000000000000000000000000000000000000

The resulting SHA-256 hash is:

    f6405ee04f91591f32f7fc78f52c7b2375822c62154a3ef53d4a6264d72185b9

## Functions (agreed with Hanson)

- `log.chain.append_entry(payload, session=None)` adds one line to the
  `log_entries` table and returns it. `payload` is a dictionary, for example
  `{"submission_id": 42, "verdict": "accepted", "time": "2026-11-12T10:00:00"}`.
  The worker calls it once after saving each verdict. Without `session`, it
  opens one with `app.db.SessionLocal`.
- `log.verify.verify_database(session=None)` reads all rows ordered by `seq`
  and returns `{"ok": true, "first_bad_seq": null}` or
  `{"ok": false, "first_bad_seq": 2}`. The route `GET /log/verify` returns this
  dictionary unchanged.

Table columns (same as the context block): `log_entries(seq, payload, prev_hash, hash)`.
`seq` is the primary key, so two workers can never write the same line number.

## Hash chain limitation

A plain hash chain detects modification, deletion of middle entries and
reordering. It cannot detect deletion of the newest entries at the end of the
log. (`tests/test_log_db.py::test_deleting_newest_row_is_NOT_caught` documents
this on purpose.) Signed checkpoints would fix this in the final project.
