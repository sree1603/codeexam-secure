"""Stand-alone demo: 10 honest programs + 1 renamed copy -> the copy ranks first.

Run:  python -m triage.demo
"""
import re
import tempfile
from pathlib import Path

from triage.report import compare_folder, print_report

SOURCE = Path("corpus/legit_programs/sum_numbers")


def main():
    folder = Path(tempfile.mkdtemp())
    for f in sorted(SOURCE.glob("*.py")):
        (folder / f.name).write_text(f.read_text())

    # Plant a copy of sol01.py with every variable renamed.
    original = (SOURCE / "sol01.py").read_text()
    renamed = original
    for old, new in [("total", "zz"), ("numbers", "qq"), ("count", "kk"), ("n", "m")]:
        renamed = re.sub(rf"\b{old}\b", new, renamed)
    (folder / "sol11_planted_copy.py").write_text("# renamed copy\n" + renamed)

    print(f"Compared {len(list(folder.glob('*.py')))} programs "
          f"({len(list(folder.glob('*.py'))) - 1} honest + 1 planted copy)")
    print_report(compare_folder(folder, top_n=5))


if __name__ == "__main__":
    main()
