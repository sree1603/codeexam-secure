#!/usr/bin/env bash
# Collects the evidence for the review (Task 9 and Card I) into docs/evidence/<time>/.
# Run from the repo folder, inside WSL:   bash scripts/collect_evidence.sh
# It asks for your Linux password once (the runner tests need sudo).
set -u
cd "$(dirname "$0")/.."
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="docs/evidence/$STAMP"
mkdir -p "$OUT"
{
  echo "date: $(date)"; echo "kernel: $(uname -a)"
  echo "python: $(python3 --version)"; echo "g++: $(g++ --version | head -1)"
  echo "cgroup filesystem: $(stat -fc %T /sys/fs/cgroup/)"
  echo "git commit: $(git rev-parse --short HEAD 2>/dev/null)"
} > "$OUT/environment.txt"
bash scripts/check_env.sh > "$OUT/check_env.txt" 2>&1
sudo .venv/bin/python -m pytest tests/test_runner.py -v > "$OUT/runner_tests.txt" 2>&1
tail -5 "$OUT/runner_tests.txt"
.venv/bin/python bench/run_attacks.py --repeat 3 --markdown "docs/attack-table.md" > "$OUT/attack_table_3_runs.txt" 2>&1
tail -15 "$OUT/attack_table_3_runs.txt"
cp results/attacks.csv "$OUT/attacks.csv" 2>/dev/null
echo
echo "Evidence saved in $OUT"
echo "Now add by hand: a screenshot of one attack being contained, and the video link."
