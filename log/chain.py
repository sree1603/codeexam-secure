import hashlib
import json

GENESIS = "0" * 64


def compute_hash(seq, payload_text, prev_hash):
    text = f"{seq}|{payload_text}|{prev_hash}"
    return hashlib.sha256(text.encode()).hexdigest()


def make_entry(seq, payload, prev_hash):
    payload_text = json.dumps(payload, sort_keys=True)

    return {
        "seq": seq,
        "payload": payload_text,
        "prev_hash": prev_hash,
        "hash": compute_hash(seq, payload_text, prev_hash)
    }


# ---------------------------------------------------------------------------
# Database part (Task 4): add a new line to the log_entries table.
# ---------------------------------------------------------------------------

def _open_default_session():
    """Open a database session using Hanson's app/db.py.

    Agreed name with Hanson: app/db.py must expose SessionLocal
    (a SQLAlchemy sessionmaker). If he uses another name, change it here.
    """
    from app.db import SessionLocal
    return SessionLocal()


def append_entry(payload, session=None):
    """Add one entry to the tamper-evident log and return it.

    payload : a dictionary (for example {"submission_id": 42, "verdict": "accepted"}).
    session : optional SQLAlchemy session. Tests pass their own session;
              the worker passes nothing and we open one from app/db.py.

    Two workers may append at the same moment. seq is the primary key, so if
    both pick the same seq, the database refuses the second one and we simply
    read the last row again and retry.
    """
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    own_session = session is None
    if own_session:
        session = _open_default_session()

    try:
        for _ in range(10):
            last = session.execute(
                text("SELECT seq, hash FROM log_entries ORDER BY seq DESC LIMIT 1")
            ).first()

            if last is None:
                seq, prev_hash = 1, GENESIS      # very first line of the log
            else:
                seq, prev_hash = last[0] + 1, last[1]

            entry = make_entry(seq, payload, prev_hash)
            try:
                session.execute(
                    text("INSERT INTO log_entries (seq, payload, prev_hash, hash) "
                         "VALUES (:seq, :payload, :prev_hash, :hash)"),
                    entry,
                )
                session.commit()
                return entry
            except IntegrityError:
                session.rollback()               # someone else took this seq; retry

        raise RuntimeError("could not append to the log after 10 tries")
    finally:
        if own_session:
            session.close()
