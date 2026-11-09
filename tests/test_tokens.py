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
