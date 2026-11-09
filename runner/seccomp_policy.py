"""The seccomp filter: kill a program that asks Linux for forbidden things.

Owner: Varshita (Person 1).  Task 6 of the guide.

A program killed by this filter ends with the signal SIGSYS
(exit code -31 in Python). The runner turns that into the violation "forbidden_call".
Method: start with a short list, make sure normal Python and C++ programs still run,
and only add more names when you understand why (use `strace` to find the call).
"""
import seccomp

# Requests (system calls) that a normal student program never needs.
BLOCKED = ["socket", "connect", "bind", "listen", "accept", "ptrace", "mount", "umount2",
           "chroot", "pivot_root", "setns", "unshare", "reboot", "init_module"]


def load_filter():
    f = seccomp.SyscallFilter(defaction=seccomp.ALLOW)  # allow everything else
    for name in BLOCKED:
        try:
            f.add_rule(seccomp.KILL, name)  # kill the program on a forbidden call
        except (RuntimeError, OSError, ValueError):
            pass  # this name does not exist on this CPU type: skip it
    f.load()
