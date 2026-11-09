from pathlib import Path
from itertools import combinations

from triage.tokens import normalize_tokens, similarity


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
