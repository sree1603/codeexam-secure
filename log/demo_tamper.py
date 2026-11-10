"""Stand-alone demo: build a log, edit one row, let the verifier catch it.

Run:  python -m log.demo_tamper
Uses a temporary database, so it never touches app.db.
"""
import os
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from log.chain import append_entry
from log.verify import verify_database


def main():
    folder = tempfile.mkdtemp()
    engine = create_engine(f"sqlite:///{os.path.join(folder, 'demo.db')}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE log_entries (seq INTEGER PRIMARY KEY, "
                          "payload TEXT, prev_hash TEXT, hash TEXT)"))
    session = sessionmaker(bind=engine)()

    print("1. Writing 3 verdicts to the log...")
    for sid, verdict in [(1, "accepted"), (2, "time_limit"), (3, "wrong_answer")]:
        e = append_entry({"submission_id": sid, "verdict": verdict}, session=session)
        print(f"   line {e['seq']}: {e['payload']}  hash={e['hash'][:12]}...")

    print("\n2. Verify the untouched log:")
    print("  ", verify_database(session))

    print("\n3. Someone secretly edits line 2 (time_limit -> accepted):")
    session.execute(text(
        "UPDATE log_entries SET payload = '{\"submission_id\": 2, \"verdict\": \"accepted\"}' "
        "WHERE seq = 2"))
    session.commit()

    print("\n4. Verify again:")
    result = verify_database(session)
    print("  ", result)
    print(f"\n   The verifier names the broken line: {result['first_bad_seq']}")


if __name__ == "__main__":
    main()
