cat > Makefile << 'EOF'
setup:
    python3 -m venv --system-site-packages .venv
    .venv/bin/pip install -r requirements.txt

test:
    .venv/bin/python -m pytest -q

run:
    .venv/bin/uvicorn app.main:app --reload --port 8000

worker:
    .venv/bin/python -m judge.worker

attacks:
    bash scripts/make_canary.sh
    .venv/bin/python bench/run_attacks.py

canary:
    bash scripts/make_canary.sh
EOF
sed -i 's/^    /\t/' Makefile