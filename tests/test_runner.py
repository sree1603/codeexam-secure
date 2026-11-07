"""Tests for the runner (Task 8). Owner: Varshita (Person 1).

Run (needs root for the real isolation, so use sudo inside WSL):
    sudo .venv/bin/python -m pytest tests/test_runner.py -v
Tests that need root or the seccomp library are SKIPPED when those are missing.
"""
import glob
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from runner.sandbox import run_request  # noqa: E402

LIMITS = {"cpu_ms": 2000, "wall_ms": 5000, "memory_mb": 256, "processes": 8, "output_kb": 1024}
IS_ROOT = os.geteuid() == 0
try:
    import seccomp  # noqa: F401
    HAS_SECCOMP = True
except ImportError:
    HAS_SECCOMP = False


def need_root():
    if not IS_ROOT:
        raise unittest.SkipTest("needs root: run with sudo")


def need_seccomp():
    if not HAS_SECCOMP:
        raise unittest.SkipTest("python3-seccomp is not installed")


def run(language, source, stdin="", limits=None):
    request = {"submission_id": "test", "language": language, "source": source,
               "limits": limits or LIMITS, "tests": [{"id": "t1", "stdin": stdin}]}
    return run_request(request)


def run_file(relative_path, limits=None):
    with open(os.path.join(REPO, relative_path), encoding="utf-8") as f:
        source = f.read()
    language = "cpp" if relative_path.endswith(".cpp") else "python"
    return run(language, source, limits=limits)["results"][0]


def scratch_folders():
    return set(glob.glob(os.path.join(tempfile.gettempdir(), "codeexam_*")))


# ---------------------------------------------------------------- normal programs
def test_normal_python_program_passes():
    result = run("python", "print(int(input()) * 2)", "21\n")["results"][0]
    assert result["stdout"] == "42\n"
    assert result["exit_code"] == 0
    assert result["violation"] is None


def test_normal_cpp_program_passes():
    source = "#include <iostream>\nint main(){int a; std::cin>>a; std::cout<<a*2<<std::endl;}"
    response = run("cpp", source, "21\n")
    assert response["compile"]["ok"] is True
    assert response["results"][0]["stdout"] == "42\n"
    assert response["results"][0]["violation"] is None


def test_cpp_compile_error_is_reported():
    response = run("cpp", "int main( { return 0; }")
    assert response["compile"]["ok"] is False
    assert response["compile"]["message"] != ""
    assert response["results"] == []


def test_several_tests_in_one_request():
    request = {"submission_id": "multi", "language": "python", "source": "print(input())",
               "limits": LIMITS, "tests": [{"id": "a", "stdin": "x\n"}, {"id": "b", "stdin": "y\n"}]}
    results = run_request(request)["results"]
    assert [r["stdout"] for r in results] == ["x\n", "y\n"]
    assert [r["id"] for r in results] == ["a", "b"]


# ---------------------------------------------------------------- limits
def test_cpu_attack_python_is_stopped():
    result = run_file("attacks/cpu/cpu1.py")
    assert "ATTACK_SUCCEEDED" not in result["stdout"]
    assert result["violation"] == "time_limit"


def test_cpu_attack_cpp_is_stopped():
    result = run_file("attacks/cpu/cpu2.cpp")
    assert "ATTACK_SUCCEEDED" not in result["stdout"]
    assert result["violation"] == "time_limit"


def test_cpu_attack_maths_is_stopped():
    result = run_file("attacks/cpu/cpu3.py")
    assert "ATTACK_SUCCEEDED" not in result["stdout"]
    assert result["violation"] == "time_limit"


def test_wall_time_limit_for_a_sleeping_program():
    limits = dict(LIMITS, wall_ms=1000)
    result = run("python", "import time\ntime.sleep(4)\nprint('late')", limits=limits)["results"][0]
    assert result["violation"] == "time_limit"
    assert result["stdout"] == ""
    assert result["wall_ms"] < 3000


def test_memory_attack_python_is_stopped():
    result = run_file("attacks/memory/mem1.py")
    assert "ATTACK_SUCCEEDED" not in result["stdout"]
    assert result["violation"] == "memory_limit"


def test_memory_attack_cpp_is_stopped():
    result = run_file("attacks/memory/mem2.cpp")
    assert "ATTACK_SUCCEEDED" not in result["stdout"]
    assert result["violation"] == "memory_limit"


def test_memory_attack_one_big_block_is_stopped():
    result = run_file("attacks/memory/mem3.py")
    assert "ATTACK_SUCCEEDED" not in result["stdout"]
    assert result["violation"] == "memory_limit"


def test_too_much_output_is_stopped():
    source = "import sys\nfor i in range(100000):\n    sys.stdout.write('x' * 100 + '\\n')\n"
    result = run("python", source)["results"][0]
    assert result["violation"] == "output_limit"
    assert len(result["stdout"]) <= LIMITS["output_kb"] * 1024


def test_process_limit_stops_many_children():
    need_root()  # the process limit only works for the user "nobody"
    source = ("import os, time\n"
              "kids = 0\n"
              "for i in range(40):\n"        # bounded: at most 40 children
              "    pid = os.fork()\n"
              "    if pid == 0:\n"
              "        time.sleep(2); os._exit(0)\n"
              "    kids += 1\n"
              "print('ATTACK_SUCCEEDED')\n")
    result = run("python", source)["results"][0]
    assert "ATTACK_SUCCEEDED" not in result["stdout"]
    assert result["violation"] == "process_limit"


# ---------------------------------------------------------------- isolation
def test_network_is_blocked_by_seccomp():
    need_root()
    need_seccomp()
    source = ("import socket\n"
              "s = socket.socket()\n"
              "print('ATTACK_SUCCEEDED')\n")
    result = run("python", source)["results"][0]
    assert "ATTACK_SUCCEEDED" not in result["stdout"]
    assert result["violation"] == "forbidden_call"
    assert result["exit_code"] == -31


def test_canary_file_cannot_be_read():
    need_root()
    path = os.path.join(tempfile.gettempdir(), "codeexam_test_canary_%d.txt" % os.getpid())
    with open(path, "w") as f:
        f.write("SECRET-test")
    os.chmod(path, 0o600)  # only the owner (root) may read it
    try:
        source = ("try:\n"
                  "    print(open(%r).read())\n"
                  "    print('ATTACK_SUCCEEDED')\n"
                  "except PermissionError:\n"
                  "    print('blocked')\n" % path)
        result = run("python", source)["results"][0]
        assert "ATTACK_SUCCEEDED" not in result["stdout"]
        assert "SECRET" not in result["stdout"]
        assert result["stdout"].strip() == "blocked"
    finally:
        os.remove(path)


def test_program_runs_as_nobody_with_private_process_list():
    need_root()
    source = "import os\nprint(os.getuid())\nprint(len(os.listdir('/proc')) < 40)\n"
    result = run("python", source)["results"][0]
    lines = result["stdout"].split()
    assert lines[0] == "65534"  # the user "nobody"


def test_scratch_folders_are_deleted():
    before = scratch_folders()
    run("python", "print('hi')")
    run("cpp", "int main( {")          # also after a compile error
    run("python", "while True: pass", limits=dict(LIMITS, cpu_ms=500, wall_ms=1000))
    assert scratch_folders() == before


def test_environment_is_clean():
    os.environ["CODEEXAM_SECRET_TEST"] = "hidden"
    try:
        source = "import os\nprint(sorted(os.environ))\n"
        result = run("python", source)["results"][0]
        assert "CODEEXAM_SECRET_TEST" not in result["stdout"]
        assert "CODEEXAM_LIMITS" not in result["stdout"]
    finally:
        del os.environ["CODEEXAM_SECRET_TEST"]
