"""Tests for the database part of the log: append_entry and verify_database."""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from log.chain import GENESIS, append_entry, compute_hash
from log.verify import verify_database


@pytest.fixture
def session(tmp_path):
    # A fresh database file with only the log_entries table (same columns as models.py).
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE log_entries (seq INTEGER PRIMARY KEY, payload TEXT, "
            "prev_hash TEXT, hash TEXT)"))
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


def test_first_entry_uses_genesis(session):
    e = append_entry({"submission_id": 1, "verdict": "accepted"}, session=session)
    assert e["seq"] == 1
    assert e["prev_hash"] == GENESIS
    assert e["hash"] == compute_hash(1, e["payload"], GENESIS)


def test_entries_are_linked(session):
    a = append_entry({"n": 1}, session=session)
    b = append_entry({"n": 2}, session=session)
    c = append_entry({"n": 3}, session=session)
    assert (a["seq"], b["seq"], c["seq"]) == (1, 2, 3)
    assert b["prev_hash"] == a["hash"]
    assert c["prev_hash"] == b["hash"]


def test_empty_log_verifies(session):
    assert verify_database(session) == {"ok": True, "first_bad_seq": None}


def test_normal_log_verifies(session):
    for i in range(3):
        append_entry({"submission_id": i, "verdict": "accepted"}, session=session)
    assert verify_database(session) == {"ok": True, "first_bad_seq": None}


def test_edited_row_is_caught_at_row_2(session):
    # This is exactly the demo: edit one row with sqlite, then verify.
    for i in range(3):
        append_entry({"submission_id": i, "verdict": "accepted"}, session=session)
    session.execute(text("UPDATE log_entries SET payload = 'x' WHERE seq = 2"))
    session.commit()
    assert verify_database(session) == {"ok": False, "first_bad_seq": 2}


def test_deleted_middle_row_is_caught(session):
    for i in range(4):
        append_entry({"n": i}, session=session)
    session.execute(text("DELETE FROM log_entries WHERE seq = 2"))
    session.commit()
    result = verify_database(session)
    assert result["ok"] is False
    assert result["first_bad_seq"] == 2


def test_deleting_newest_row_is_NOT_caught(session):
    # Known limit of a plain hash chain (written in contracts/log_entry.md).
    for i in range(3):
        append_entry({"n": i}, session=session)
    session.execute(text("DELETE FROM log_entries WHERE seq = 3"))
    session.commit()
    assert verify_database(session)["ok"] is True
