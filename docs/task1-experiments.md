# Task 1: the four building blocks (Varshita's notes)

I ran all four experiments in Ubuntu 24.04 on WSL2 (user `sree`, project folder `~/codeexam-secure`, virtual environment active). The commands, what I saw and what each one means for our runner are below.

## Experiment 1: limit memory for one command

```text
(ulimit -v 200000; python3 -c "x = bytearray(500*1024*1024)")
```

**What I saw:** Python stopped with a `MemoryError` on the line `x = bytearray(500*1024*1024)`.

**What it means:** `ulimit -v 200000` limits the program's address space to about 200 MB (the number is in kilobytes). The program asked for 500 MB, so Linux refused and Python raised `MemoryError`. The limit only works inside the brackets, so it did not change my normal terminal. Our runner uses the same kind of limit (`RLIMIT_AS`, set with Python's `resource` module) to stop memory attacks such as `mem1.py` and `mem3.py`.

## Experiment 2: a private process list and no network

```text
sudo unshare --pid --fork --mount-proc --net bash
ps aux
ping -c 1 8.8.8.8
exit
```

**What I saw:**

- `ps aux` listed only two processes: `bash` with PID 1 and `ps aux` itself with PID 7. The normal machine has many more.
- `ping -c 1 8.8.8.8` printed `ping: connect: Network is unreachable`.

**What it means:** `unshare` gave the new shell its own private view of the machine. `--pid --mount-proc` gave it its own process list, so it cannot see or touch the other programs on my computer. `--net` gave it an empty network, so it cannot reach the internet or other computers. Our runner starts every student program this way. One extra thing I noticed: inside the private view the first program (`bash`) is PID 1. Linux ignores most kill signals for PID 1, so in the runner the student program must run as a child, not as PID 1 (see `docs/known-weaknesses.md`, point 11).

## Experiment 3: see what a program asks Linux to do

```text
strace -f -o /tmp/trace.txt python3 -c "print('hi')"
head -50 /tmp/trace.txt
```

**What I saw:** the program printed `hi`, and the first 50 lines of `/tmp/trace.txt` were requests such as `execve` (start the program), `brk` and `mmap` (get memory), `openat` and `read` (open and read library files like `libc.so.6`) and `close`. The first line shows that `python3` started from my project's `.venv`.

**What it means:** every request a program makes to Linux is a *system call*, and each has a name. A simple `print` already needs many of them. The seccomp filter in our runner works on these names: it kills a program that uses a forbidden name such as `socket` or `connect`, and allows the rest. `strace` is how I find out which call a normal program needs when the filter kills it by mistake.

## Experiment 4: are control groups (cgroups) available?

```text
stat -fc %T /sys/fs/cgroup/
```

**What I saw:** `cgroup2fs`

**What it means:** cgroup version 2 is available on my WSL. Control groups can limit memory for a whole group of processes, which the simple `ulimit`-style limits cannot do. The prototype does not depend on it, so cgroups stay a stretch goal (see the end of `docs/known-weaknesses.md`).

## Answer to share with the team

My WSL has cgroup v2 (`cgroup2fs`), the memory limit and the private process list and empty network all worked. The prototype runner will use `unshare`, a limit on memory and CPU, the user `nobody` and a seccomp filter. Cgroups are optional.