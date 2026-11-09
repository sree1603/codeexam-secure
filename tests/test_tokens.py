import tempfile
import unittest
from pathlib import Path

from triage.tokens import normalize_tokens, ngrams, similarity
from triage.report import compare_folder


class TestSimilarity(unittest.TestCase):

    def test_variable_names_are_normalized(self):
        code1 = "total = 10\nprint(total)"
        code2 = "answer = 50\nprint(answer)"

        self.assertEqual(
            normalize_tokens(code1),
            normalize_tokens(code2)
        )

    def test_comments_are_ignored(self):
        code1 = "x = 10\nprint(x)"
        code2 = "# A comment\ny = 20\nprint(y)"

        self.assertEqual(
            normalize_tokens(code1),
            normalize_tokens(code2)
        )

    def test_ngrams(self):
        tokens = ["a", "b", "c", "d", "e"]

        self.assertEqual(len(ngrams(tokens, 3)), 3)

    def test_identical_programs_have_full_similarity(self):
        tokens = normalize_tokens("x = 10\nprint(x)")

        self.assertEqual(similarity(tokens, tokens), 1.0)

    def test_empty_programs(self):
        self.assertEqual(similarity([], []), 0.0)

    def test_copied_program_ranks_first(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)

            (folder / "original.py").write_text(
                "total = 0\n"
                "for number in range(10):\n"
                "    total += number\n"
                "print(total)\n"
            )

            (folder / "copied.py").write_text(
                "# Changed variable names\n"
                "answer = 0\n"
                "for value in range(20):\n"
                "    answer += value\n"
                "print(answer)\n"
            )

            (folder / "different.py").write_text(
                "def greet(name):\n"
                "    print('Hello', name)\n"
            )

            results = compare_folder(folder)

            self.assertTrue(results)
            self.assertEqual(
                {Path(results[0]["file_a"]).name,
                 Path(results[0]["file_b"]).name},
                {"original.py", "copied.py"}
            )


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Tests for the API-format ranking and the database reader (Task 7)
# ---------------------------------------------------------------------------
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from triage.report import rank_pairs, similarity_for_problem
from triage.tokens import safe_tokens

ORIGINAL = "total = 0\nfor number in range(10):\n    total += number\nprint(total)\n"
RENAMED = "s = 0\nfor v in range(99):\n    s += v\nprint(s)\n"
OTHER = "def greet(name):\n    print('Hello', name)\n"


def test_rank_pairs_uses_api_format():
    pairs = rank_pairs({1: ORIGINAL, 2: OTHER, 3: RENAMED})
    assert set(pairs[0]) == {"a", "b", "score"}
    assert (pairs[0]["a"], pairs[0]["b"]) == (1, 3)      # the renamed copy is first
    assert pairs[0]["score"] == 1.0


def test_rank_pairs_top_n():
    programs = {i: ORIGINAL for i in range(6)}
    assert len(rank_pairs(programs, top_n=4)) == 4


def test_broken_code_does_not_crash():
    assert safe_tokens("print((1, 2") == []
    pairs = rank_pairs({1: ORIGINAL, 2: "print((1, 2", 3: RENAMED})
    assert (pairs[0]["a"], pairs[0]["b"]) == (1, 3)


def test_similarity_for_problem_reads_only_python_of_that_problem(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 't.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE submissions (id INTEGER PRIMARY KEY, "
                          "problem_id INTEGER, language TEXT, source TEXT)"))
        rows = [(42, 1, "python", ORIGINAL), (57, 1, "python", RENAMED),
                (58, 1, "python", OTHER), (59, 1, "cpp", ORIGINAL),
                (60, 2, "python", ORIGINAL)]
        for r in rows:
            conn.execute(text("INSERT INTO submissions VALUES (:a,:b,:c,:d)"),
                         dict(zip("abcd", r)))
    session = sessionmaker(bind=engine)()
    result = similarity_for_problem(1, session=session)
    session.close()
    assert result[0] == {"a": 42, "b": 57, "score": 1.0}
    assert all(p["a"] not in (59, 60) and p["b"] not in (59, 60) for p in result)
