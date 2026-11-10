#!/usr/bin/env bash
# The Friday integration run (Team Lead). Run on a clean copy of main:
#     bash scripts/friday_integration.sh
cd "$(dirname "$0")/.." || exit 1
set -e
git checkout main
git pull
source .venv/bin/activate
pip install -q -r requirements.txt
bash scripts/check_env.sh
echo "--- running all tests (runner tests need sudo; they are skipped without it) ---"
python -m pytest -q
echo "--- runner tests as root ---"
sudo .venv/bin/python -m pytest tests/test_runner.py -q
echo
echo "Now do ONE submission by hand: make run (terminal 1), make worker (terminal 2), then submit in the browser."
echo "Questions for the team: did all tests pass? did a submission reach a verdict? did anyone change a contract?"
