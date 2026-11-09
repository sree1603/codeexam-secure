from log.chain import GENESIS, compute_hash


def verify_entries(entries):
    expected_prev_hash = GENESIS

    for expected_seq, entry in enumerate(entries, start=1):

        if entry["seq"] != expected_seq:
            return False, expected_seq

        if entry["prev_hash"] != expected_prev_hash:
            return False, expected_seq

        calculated_hash = compute_hash(
            entry["seq"],
            entry["payload"],
            entry["prev_hash"]
        )

        if entry["hash"] != calculated_hash:
            return False, expected_seq

        expected_prev_hash = entry["hash"]

    return True, None


def verify_database(session=None):
    """Check the whole log_entries table (Task 6).

    Returns {"ok": True/False, "first_bad_seq": None or the first bad line number}.
    Hanson's route GET /log/verify returns this dictionary as it is.
    """
    from sqlalchemy import text

    own_session = session is None
    if own_session:
        from log.chain import _open_default_session
        session = _open_default_session()

    try:
        rows = session.execute(
            text("SELECT seq, payload, prev_hash, hash FROM log_entries ORDER BY seq")
        ).all()
    finally:
        if own_session:
            session.close()

    entries = [
        {"seq": r[0], "payload": r[1], "prev_hash": r[2], "hash": r[3]}
        for r in rows
    ]
    ok, first_bad_seq = verify_entries(entries)
    return {"ok": ok, "first_bad_seq": first_bad_seq}


if __name__ == "__main__":
    # Quick check from the terminal:  python -m log.verify
    import json
    print(json.dumps(verify_database()))
