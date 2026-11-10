"""Starts the student program with all protections. Runs as root, ends as "nobody".

Owner: Varshita (Person 1).  Tasks 5 and 6 of the guide.

Order of work (this order matters):
  1. switch to the user "nobody"            (we lose our power)
  2. load the seccomp filter                (stays active after execvpe)
  3. apply the resource limits              (CPU, memory, processes, file size)
  4. start the student command as a child and report how it ended

It is started by runner/sandbox.py as:
    python -I runner/child_launcher.py -- <student command>
The "-I" (isolated) option stops Python from importing files from the scratch folder.
"""
import os
import sys

# Make "runner" importable without using the current folder (the scratch folder).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json  # noqa: E402

from runner.sandbox import clean_env, drop_to_nobody, make_limit_setter  # noqa: E402

try:  # imported BEFORE we lose power
    from runner.seccomp_policy import load_filter
except ImportError:
    load_filter = None


def fail(message):
    sys.stderr.write("launcher_error: %s\n" % message)
    os._exit(111)  # fail closed: never run the program without protection


def main():
    command = sys.argv[sys.argv.index("--") + 1:]
    limits = json.loads(os.environ.pop("CODEEXAM_LIMITS", "{}"))
    workdir = os.environ.get("CODEEXAM_WORKDIR", os.getcwd())
    allow_no_seccomp = os.environ.get("CODEEXAM_ALLOW_NO_SECCOMP") == "1"

    if os.geteuid() == 0:
        drop_to_nobody()
        if os.getuid() == 0 or os.geteuid() == 0:
            fail("could not drop root")
        try:
            os.setuid(0)  # must FAIL: we must not be able to get power back
            fail("root could be regained")
        except PermissionError:
            pass

    if load_filter is None:
        if not allow_no_seccomp:
            fail("seccomp library missing (sudo apt install python3-seccomp)")
    else:
        try:
            load_filter()  # the filter stays active after execvp
        except Exception as error:  # noqa: BLE001
            fail("seccomp filter failed: %s" % error)

    make_limit_setter(limits.get("cpu_s", 2), limits.get("memory_mb", 256),
                      limits.get("processes", 0), limits.get("output_kb", 1024))()

    # Why fork? Inside the private process list this program is number 1, and Linux
    # ignores most kill signals sent to number 1 (for example the CPU-time signal).
    # So the student program runs as a CHILD, and we wait for it and pass on how it ended.
    pid = os.fork()
    if pid == 0:
        try:
            os.execvpe(command[0], command, clean_env(workdir))
        except OSError as error:
            fail("cannot start program: %s" % error)
    _, status = os.waitpid(pid, 0)
    if os.WIFSIGNALED(status):
        os._exit(128 + os.WTERMSIG(status))  # the usual way to report "killed by signal"
    os._exit(os.WEXITSTATUS(status))


main()
