"""Attack harness (Card E): run every attack against three ways of running code.

Owner: Varshita (Person 1).

    python bench/run_attacks.py                       # all attacks, all runners
    python bench/run_attacks.py --runners ours        # only our locked box
    python bench/run_attacks.py --only cpu,memory     # only some categories
    python bench/run_attacks.py --repeat 3 --markdown docs/attack-table.md

RULE: an attack is CONTAINED if its output does NOT contain ATTACK_SUCCEEDED.

Runners:
  naive   baselines/naive.py       (Trisha)  plain subprocess, no limits except a timeout
  docker  baselines/docker_runner.py (Trisha) Docker with a 256 MB memory limit
  ours    runner/run_cli.py        (Varshita) the locked box, started with sudo like the worker does

Run it ONLY inside your own WSL Ubuntu. If something hangs press Ctrl+C and run:
    pkill -f attacks/
"""
import argparse
import csv
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

MARKER = "ATTACK_SUCCEEDED"
ATTACK_TIMEOUT_S = 15
CATEGORIES = ["cpu", "memory", "process", "network", "files"]
RUNNERS = ["naive", "docker", "ours"]
SKIP_NAMES = {"listener.py", "README.md", ".gitkeep", "__init__.py"}
BUILD_DIR = os.path.join(REPO, "results", "build")
LIMITS = {"cpu_ms": 2000, "wall_ms": 5000, "memory_mb": 256, "processes": 8, "output_kb": 1024}


# ---------------------------------------------------------------- finding attacks
def find_attacks(only):
    attacks = []
    for category in CATEGORIES:
        if only and category not in only:
            continue
        folder = os.path.join(REPO, "attacks", category)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name in SKIP_NAMES or not name.endswith((".py", ".cpp")):
                continue
            attacks.append({"name": name, "category": category,
                            "path": os.path.join(folder, name)})
    return attacks


def build_binary(attack):
    """Compile a C++ attack to a static binary (used by naive and docker)."""
    os.makedirs(BUILD_DIR, exist_ok=True)
    binary = os.path.join(BUILD_DIR, attack["name"].replace(".cpp", ""))
    done = subprocess.run(["g++", "-O2", "-static", "-o", binary, attack["path"]],
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError("compile failed: " + done.stderr[:300])
    return binary


# ---------------------------------------------------------------- the three runners
def run_naive(attack):
    from baselines.naive import run_naive as naive  # Trisha's file
    command = ["python3", attack["path"]] if attack["path"].endswith(".py") \
        else [build_binary(attack)]
    r = naive(command, "", timeout_s=ATTACK_TIMEOUT_S)
    return r["stdout"], "exit=%s%s" % (r["exit_code"], " TIMEOUT" if r.get("timed_out") else "")


def run_docker(attack):
    if attack["path"].endswith(".py"):
        from baselines.docker_runner import run_docker as docker  # Trisha's file
        folder, name = os.path.split(attack["path"])
        r = docker(folder, name, timeout_s=ATTACK_TIMEOUT_S)
        return r["stdout"], "exit=%s" % r["exit_code"]
    binary = build_binary(attack)  # C++: same Docker settings, but run the binary
    folder, name = os.path.split(binary)
    done = subprocess.run(["docker", "run", "--rm", "--memory=256m", "-v", "%s:/work:ro" % folder,
                           "python:3.12-slim", "/work/" + name],
                          capture_output=True, text=True, timeout=ATTACK_TIMEOUT_S)
    return done.stdout, "exit=%s" % done.returncode


def run_ours(attack):
    with open(attack["path"], encoding="utf-8") as f:
        source = f.read()
    request = {"submission_id": "attack-" + attack["name"],
               "language": "python" if attack["path"].endswith(".py") else "cpp",
               "source": source, "limits": LIMITS, "tests": [{"id": "t1", "stdin": ""}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(request, f)
        request_path = f.name
    try:
        venv_python = os.path.join(REPO, ".venv", "bin", "python")
        python = venv_python if os.path.exists(venv_python) else sys.executable
        command = [python, "-m", "runner.run_cli", request_path]
        if os.geteuid() != 0:
            command = ["sudo", "-n"] + command  # same way the worker calls the runner
        done = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=60)
        if done.returncode != 0:
            raise RuntimeError("runner failed (is sudo set up? run scripts/setup_sudoers.sh): "
                               + (done.stdout + done.stderr)[:300])
        response = json.loads(done.stdout)
        if not response["compile"]["ok"]:
            raise RuntimeError("compile failed: " + response["compile"]["message"][:200])
        result = response["results"][0]
        return result["stdout"], "exit=%s violation=%s" % (result["exit_code"], result["violation"])
    finally:
        os.remove(request_path)


RUNNER_FUNCTIONS = {"naive": run_naive, "docker": run_docker, "ours": run_ours}


# ---------------------------------------------------------------- helpers
def available_mb():
    """Free memory the system can still give out (from /proc/meminfo)."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return -1


def make_canary():
    script = os.path.join(REPO, "scripts", "make_canary.sh")
    if os.path.exists(script):
        subprocess.run(["bash", script], cwd=REPO, capture_output=True)
        return
    with open("/tmp/canary_secret.txt", "w") as f:  # fallback if Trisha's script is missing
        f.write("SECRET-%d\n" % int(time.time()))
    os.chmod("/tmp/canary_secret.txt", 0o600)


def start_listener():
    path = os.path.join(REPO, "attacks", "network", "listener.py")
    if not os.path.exists(path):
        return None
    process = subprocess.Popen([sys.executable, path], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    time.sleep(0.5)  # give it time to start listening on port 9999
    return process


def stop_listener(process):
    if process is not None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()


def control_check(runner):
    """Run a harmless program through the runner. Returns an error text, or None if it works.

    Without this check a broken runner (for example Docker that is not running) prints
    nothing, and nothing printed would wrongly look like CONTAINED.
    """
    os.makedirs(BUILD_DIR, exist_ok=True)
    path = os.path.join(BUILD_DIR, "control.py")
    with open(path, "w") as f:
        f.write('print("CONTROL_OK")\n')
    try:
        output, _note = RUNNER_FUNCTIONS[runner]({"name": "control.py", "category": "control", "path": path})
    except Exception as error:  # noqa: BLE001
        return str(error).splitlines()[0][:100] if str(error) else "runner raised an error"
    return None if "CONTROL_OK" in (output or "") else "a harmless program printed nothing"


def run_matrix(attacks, runners, broken):
    """Returns {attack_name: {"category":..., runner: "CONTAINED"|"NOT_CONTAINED"|"ERROR: ..."}}"""
    results = {}
    make_canary()
    for attack in attacks:
        row = {"category": attack["category"]}
        for runner in runners:
            if runner in broken:
                row[runner] = "ERROR: " + broken[runner]
                continue
            make_canary()  # a fresh canary before every run
            listener = start_listener() if attack["category"] == "network" else None
            note = ""
            memory_before = available_mb()
            try:
                output, note = RUNNER_FUNCTIONS[runner](attack)
                row[runner] = "NOT_CONTAINED" if MARKER in (output or "") else "CONTAINED"
            except subprocess.TimeoutExpired:
                row[runner] = "CONTAINED"  # it never finished, so it never printed the marker
                note = "TIMEOUT"
            except Exception as error:  # noqa: BLE001
                row[runner] = "ERROR: %s" % str(error).splitlines()[0][:80] if str(error) else "ERROR"
            finally:
                stop_listener(listener)
            print("  %-8s %-14s %-14s %s  free_before=%dMB" % (
                runner, attack["name"], short(row[runner]), note, memory_before), flush=True)
        results[attack["name"]] = row
    return results


# ---------------------------------------------------------------- output
def short(value):
    if value.startswith("ERROR"):
        return "ERROR"
    return value


def print_table(results, runners):
    header = ["attack", "category"] + runners
    rows = [[name, row["category"]] + [short(row.get(r, "-")) for r in runners]
            for name, row in results.items()]
    widths = [max(len(str(x)) for x in col) for col in zip(header, *rows)]
    line = "  ".join("%-*s" % (w, h) for w, h in zip(widths, header))
    print(line)
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join("%-*s" % (w, c) for w, c in zip(widths, row)))
    for r in runners:
        stopped = sum(1 for row in results.values() if row.get(r) == "CONTAINED")
        errors = sum(1 for row in results.values() if str(row.get(r, "")).startswith("ERROR"))
        print("%s: %d of %d contained%s" % (r, stopped, len(results),
                                            (" (%d errors)" % errors) if errors else ""))


def write_csv(results, runners):
    os.makedirs(os.path.join(REPO, "results"), exist_ok=True)
    path = os.path.join(REPO, "results", "attacks.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["attack", "category"] + RUNNERS)
        for name, row in results.items():
            writer.writerow([name, row["category"]] + [short(row.get(r, "NOT_RUN")) for r in RUNNERS])
    print("written:", os.path.relpath(path, REPO))


def write_markdown(results, runners, path, stable_note):
    full = os.path.join(REPO, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    total = len(results)
    lines = ["# Attack table", "",
             "Each row is one attack program. **CONTAINED** means the attack did not print "
             "`ATTACK_SUCCEEDED`. **NOT_CONTAINED** means the attack reached its goal.", "",
             "| attack | category | " + " | ".join(runners) + " |",
             "|---|---|" + "---|" * len(runners)]
    for name, row in results.items():
        lines.append("| %s | %s | %s |" % (name, row["category"],
                                           " | ".join(short(row.get(r, "-")) for r in runners)))
    lines += ["", "## Reading the table", ""]
    for r in runners:
        stopped = sum(1 for row in results.values() if row.get(r) == "CONTAINED")
        lines.append("- **%s** contained %d of %d attacks." % (r, stopped, total))
        missed = [n for n, row in results.items() if row.get(r) == "NOT_CONTAINED"]
        if missed:
            lines.append("  - not contained: " + ", ".join(missed))
    lines += ["", stable_note, "",
              "TODO (write by hand): one honest paragraph. Say which attacks Docker or our box "
              "missed and why. Do not hide a failure.", ""]
    with open(full, "w") as f:
        f.write("\n".join(lines))
    print("written:", path)


def main():
    parser = argparse.ArgumentParser(description="Run all attacks against all runners.")
    parser.add_argument("--runners", default=",".join(RUNNERS))
    parser.add_argument("--only", default="")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--markdown", default="")
    args = parser.parse_args()
    runners = [r for r in args.runners.split(",") if r in RUNNERS]
    only = [c for c in args.only.split(",") if c]

    attacks = find_attacks(only)
    if not attacks:
        print("No attack files found under attacks/. Ask the others to merge their attacks first.")
        return 1
    print("Found %d attacks. Running on: %s" % (len(attacks), ", ".join(runners)))
    broken = {}
    for runner in runners:
        problem = control_check(runner)
        if problem:
            broken[runner] = problem
            print("WARNING: runner '%s' does not work, so it is skipped: %s" % (runner, problem))
    all_runs = []
    for n in range(args.repeat):
        print("\n=== run %d of %d ===" % (n + 1, args.repeat))
        all_runs.append(run_matrix(attacks, runners, broken))
    results = all_runs[-1]
    print()
    print_table(results, runners)
    write_csv(results, runners)

    stable = all(run == all_runs[0] for run in all_runs)
    note = ("Stability: the table was identical in all %d runs." % args.repeat) if stable else \
           ("WARNING: the %d runs gave different results. Find out why (often a leftover "
            "process: run `pkill -f attacks/`) before using this table." % args.repeat)
    if args.repeat > 1:
        print(note)
    if args.markdown:
        write_markdown(results, runners, args.markdown, note)
    return 0 if stable else 2


if __name__ == "__main__":
    sys.exit(main())
