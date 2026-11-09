"""The runner: runs one submission inside the locked box and returns the RESPONSE.

Owner: Varshita (Person 1).  Tasks 4, 5 and 7 of the guide.

How one test runs (isolated mode, needs root, so start it with sudo inside WSL):
  1. a fresh scratch folder is made and the student's file is written into it
  2. (C++ only) the file is compiled as the user "nobody"
  3. `unshare` gives the program a private process list and NO network
  4. runner/child_launcher.py drops power to "nobody", loads the seccomp filter,
     applies the resource limits and then replaces itself with the student program
  5. we wait for it, and kill the whole group if it takes too long
  6. the scratch folder is always deleted at the end

If we are NOT root (for example on a laptop without sudo) the runner still works
but only with plain limits and WITHOUT the private views and the safe user.
"""
import json
import os
import pwd
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCHER = os.path.join(REPO_ROOT, "runner", "child_launcher.py")

DEFAULT_LIMITS = {"cpu_ms": 2000, "wall_ms": 5000, "memory_mb": 256,
                  "processes": 8, "output_kb": 1024}
COMPILE_TIMEOUT_S = 10
SAFE_PATH = "/usr/local/bin:/usr/bin:/bin"


# ---------------------------------------------------------------- limits
def make_limit_setter(cpu_s, mem_mb, procs, fsize_kb, nofile=64):
    """Return a function that applies the limits to the CURRENT process.

    Used (a) by the launcher just before it starts the student program and
    (b) as preexec_fn when compiling. Limits are inherited by the program.
    """
    def apply():
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s + 1))
        if mem_mb:
            limit = mem_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        if procs:
            resource.setrlimit(resource.RLIMIT_NPROC, (procs, procs))
        resource.setrlimit(resource.RLIMIT_FSIZE, (fsize_kb * 1024, fsize_kb * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (nofile, nofile))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))  # no core dump files
    return apply


def drop_to_nobody():
    """Give up root power. Does nothing when we are not root."""
    if os.geteuid() != 0:
        return
    user = pwd.getpwnam("nobody")
    os.setgroups([])
    os.setgid(user.pw_gid)
    os.setuid(user.pw_uid)


def clean_env(workdir):
    """The small, safe set of environment variables the student program gets."""
    return {"PATH": SAFE_PATH, "HOME": workdir, "TMPDIR": workdir,
            "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}


# ---------------------------------------------------------------- helpers
def _give_to_nobody(path):
    if os.geteuid() == 0:
        user = pwd.getpwnam("nobody")
        os.chown(path, user.pw_uid, user.pw_gid)


def can_isolate():
    return os.geteuid() == 0 and shutil.which("unshare") is not None


def _classify(code, timed_out, stderr_text, stdout_size, limits, cpu_ms):
    """Turn what we saw into a short violation text (or None)."""
    if timed_out:
        return "time_limit"
    if code == -signal.SIGXCPU:
        return "time_limit"
    if code == -signal.SIGSYS:
        return "forbidden_call"
    if code == -signal.SIGXFSZ or "File too large" in stderr_text \
            or stdout_size >= limits["output_kb"] * 1024:
        return "output_limit"
    if "MemoryError" in stderr_text or "bad_alloc" in stderr_text \
            or "Cannot allocate memory" in stderr_text:
        return "memory_limit"
    if "Resource temporarily unavailable" in stderr_text \
            or "can't start new thread" in stderr_text or "Cannot fork" in stderr_text:
        return "process_limit"
    if "Network is unreachable" in stderr_text:
        return "network_blocked"
    if code == -signal.SIGKILL:
        # Killed by the kernel: either the CPU hard limit or running out of memory.
        return "time_limit" if cpu_ms >= limits["cpu_ms"] else "memory_limit"
    if stderr_text.startswith("launcher_error"):
        return "launcher_error"
    return None


def _decode_status(status):
    """Exit code of the launcher. The launcher reports "killed by signal N" as 128 + N."""
    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    code = os.WEXITSTATUS(status)
    if code > 128 and (code - 128) in (
            signal.SIGKILL, signal.SIGXCPU, signal.SIGXFSZ, signal.SIGSYS,
            signal.SIGABRT, signal.SIGSEGV, signal.SIGBUS, signal.SIGFPE, signal.SIGILL):
        return -(code - 128)
    return code


# ---------------------------------------------------------------- one test
def run_program(command, stdin_text, limits, workdir, outdir, isolated=None):
    """Run one program once. Returns a dict (stdout, stderr, cpu_ms, ...)."""
    if isolated is None:
        isolated = can_isolate()
    stdin_path = os.path.join(outdir, "stdin.txt")
    stdout_path = os.path.join(outdir, "stdout.txt")
    stderr_path = os.path.join(outdir, "stderr.txt")
    with open(stdin_path, "w", encoding="utf-8") as f:
        f.write(stdin_text or "")

    cpu_s = (limits["cpu_ms"] + 999) // 1000
    env = {"PATH": SAFE_PATH,
           "CODEEXAM_LIMITS": json.dumps({
               "cpu_s": cpu_s, "memory_mb": limits["memory_mb"],
               # the process limit counts all processes of the user "nobody",
               # so we only use it when we really become "nobody"
               "processes": limits["processes"] if isolated else 0,
               "output_kb": limits["output_kb"]}),
           "CODEEXAM_WORKDIR": workdir}
    if os.environ.get("CODEEXAM_ALLOW_NO_SECCOMP"):
        env["CODEEXAM_ALLOW_NO_SECCOMP"] = os.environ["CODEEXAM_ALLOW_NO_SECCOMP"]

    prefix = ["unshare", "--pid", "--fork", "--mount-proc", "--net"] if isolated else []
    full_command = prefix + [sys.executable, "-I", LAUNCHER, "--"] + command

    start = time.time()
    with open(stdin_path, "rb") as fin, open(stdout_path, "wb") as fout, \
            open(stderr_path, "wb") as ferr:
        proc = subprocess.Popen(full_command, stdin=fin, stdout=fout, stderr=ferr,
                                cwd=workdir, env=env, start_new_session=True)
        deadline = start + limits["wall_ms"] / 1000.0
        timed_out = False
        try:
            while True:
                pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
                if pid:
                    break
                if time.time() > deadline:
                    timed_out = True
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)  # kill the whole group
                    except ProcessLookupError:
                        pass
                    pid, status, usage = os.wait4(proc.pid, 0)
                    break
                time.sleep(0.005)
        finally:
            proc.returncode = 0  # we reaped it ourselves with wait4
            try:  # kill any leftovers (for example children the program started)
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    wall_ms = int((time.time() - start) * 1000)

    cap = limits["output_kb"] * 1024
    stdout_size = os.path.getsize(stdout_path)
    with open(stdout_path, "rb") as f:
        stdout = f.read(cap).decode("utf-8", errors="replace")
    with open(stderr_path, "rb") as f:
        stderr = f.read()[-4000:].decode("utf-8", errors="replace")
    code = _decode_status(status)
    cpu_ms = int((usage.ru_utime + usage.ru_stime) * 1000)
    return {"stdout": stdout, "stderr": stderr, "exit_code": code,
            "timed_out": timed_out, "cpu_ms": cpu_ms, "wall_ms": wall_ms,
            "peak_kb": int(usage.ru_maxrss), "stdout_size": stdout_size}


# ---------------------------------------------------------------- compile
def compile_cpp(workdir):
    """Compile main.cpp as the user nobody. Returns (ok, message)."""
    setter = make_limit_setter(cpu_s=COMPILE_TIMEOUT_S, mem_mb=2048, procs=64,
                               fsize_kb=65536, nofile=256)

    def prepare():
        setter()
        drop_to_nobody()

    try:
        done = subprocess.run(["g++", "-O2", "-o", "main", "main.cpp"], cwd=workdir,
                              env=clean_env(workdir), capture_output=True, text=True,
                              timeout=COMPILE_TIMEOUT_S, preexec_fn=prepare)
    except subprocess.TimeoutExpired:
        return False, "compile timed out"
    if done.returncode != 0:
        return False, (done.stderr or "compile failed")[:2000]
    return True, ""


# ---------------------------------------------------------------- request
def run_request(request):
    """RUNNER CONTRACT: REQUEST dict in, RESPONSE dict out."""
    language = request.get("language")
    if language not in ("python", "cpp"):
        raise ValueError("language must be 'python' or 'cpp'")
    limits = dict(DEFAULT_LIMITS)
    limits.update(request.get("limits") or {})
    isolated = can_isolate()

    workdir = tempfile.mkdtemp(prefix="codeexam_run_")
    outdir = tempfile.mkdtemp(prefix="codeexam_out_")  # only root can use this one
    try:
        _give_to_nobody(workdir)
        os.chmod(workdir, 0o755)
        filename = "main.py" if language == "python" else "main.cpp"
        source_path = os.path.join(workdir, filename)
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(request.get("source", ""))
        os.chmod(source_path, 0o644)
        _give_to_nobody(source_path)

        response = {"submission_id": request.get("submission_id"),
                    "compile": {"ok": True, "message": ""}, "results": []}
        if language == "cpp":
            ok, message = compile_cpp(workdir)
            response["compile"] = {"ok": ok, "message": message}
            if not ok:
                return response
            command = ["./main"]
        else:
            command = ["python3", "main.py"]

        for test in request.get("tests", []):
            r = run_program(command, test.get("stdin", ""), limits, workdir, outdir, isolated)
            response["results"].append({
                "id": test.get("id"), "stdout": r["stdout"], "cpu_ms": r["cpu_ms"],
                "wall_ms": r["wall_ms"], "peak_kb": r["peak_kb"],
                "exit_code": r["exit_code"],
                "violation": _classify(r["exit_code"], r["timed_out"], r["stderr"],
                                       r["stdout_size"], limits, r["cpu_ms"])})
        return response
    finally:  # cleanup ALWAYS happens, even after an error
        shutil.rmtree(workdir, ignore_errors=True)
        shutil.rmtree(outdir, ignore_errors=True)
