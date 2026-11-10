from pathlib import Path
from itertools import combinations

from triage.tokens import normalize_tokens, safe_tokens, similarity


def compare_folder(folder, top_n=10):
    """
    Compare all Python files in a folder.

    Returns the most similar pairs, sorted by similarity score.
    """
    folder = Path(folder)
    programs = {}

    for file_path in sorted(folder.rglob("*.py")):
        source = file_path.read_text(encoding="utf-8")
        programs[str(file_path)] = normalize_tokens(source)

    results = []

    for file_a, file_b in combinations(programs, 2):
        score = similarity(programs[file_a], programs[file_b])

        results.append({
            "file_a": file_a,
            "file_b": file_b,
            "score": score,
        })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:top_n]


def rank_pairs(programs, top_n=10):
    """Rank pairs of programs by similarity.

    programs : dictionary {submission_id: python source text}
    Returns the top pairs as [{"a": 42, "b": 57, "score": 0.91}, ...],
    the format of GET /similarity/{problem_id} in contracts/api.md.
    """
    tokens = {key: safe_tokens(source) for key, source in programs.items()}

    pairs = []
    for a, b in combinations(sorted(tokens), 2):
        pairs.append({"a": a, "b": b, "score": round(similarity(tokens[a], tokens[b]), 4)})

    pairs.sort(key=lambda item: item["score"], reverse=True)
    return pairs[:top_n]


def similarity_for_problem(problem_id, session=None, top_n=10):
    """Read the Python submissions of one problem from the database and rank them.

    Hanson's route GET /similarity/{problem_id} returns this list as it is.
    Only Python is supported in the prototype.
    """
    from sqlalchemy import text

    own_session = session is None
    if own_session:
        from log.chain import _open_default_session
        session = _open_default_session()

    try:
        rows = session.execute(
            text("SELECT id, source FROM submissions "
                 "WHERE problem_id = :pid AND language = 'python' ORDER BY id"),
            {"pid": problem_id},
        ).all()
    finally:
        if own_session:
            session.close()

    return rank_pairs({row[0]: row[1] for row in rows}, top_n)


def print_report(results):
    """Print a readable similarity report."""
    if not results:
        print("No program pairs found.")
        return

    print("\nSIMILARITY REPORT")
    print("-" * 60)

    for rank, result in enumerate(results, start=1):
        print(f"\nRank: {rank}")
        print(f"Program 1: {result['file_a']}")
        print(f"Program 2: {result['file_b']}")
        print(f"Similarity: {result['score']:.2%}")

    print("\nNote: High similarity is a reason for review, not proof of cheating.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare Python programs for similarity."
    )
    parser.add_argument("folder", help="Folder containing Python programs")
    parser.add_argument("--top", type=int, default=10,
                        help="Number of pairs to display")

    args = parser.parse_args()

    if args.top <= 0:
        parser.error("--top must be greater than zero")

    report = compare_folder(args.folder, args.top)
    print_report(report)
