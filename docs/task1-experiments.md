# Task 1: the four building blocks (Varshita's notes)

I ran all four experiments in Ubuntu (WSL2) on my own computer, inside `~/codeexam-secure`.
Below is what I typed, what I saw, and what it means for our runner.

## Experiment 1: limit memory for one command

```text
(ulimit -v 200000; python3 -c "x = bytearray(500*1024*1024)")
```

**What I saw:**

```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    x = bytearray(500*1024*1024)
MemoryError
```

**What it means:** `ulimit -v 200000` limits the memory a program may use to about 200 MB (the number is in kilobytes). The program asked for 500 MB, so Linux refused and Python raised `MemoryError`. The limit only applies to this one command, because I put it inside `( ... )`. Our runner uses the same idea in Python with `resource.setrlimit(RLIMIT_AS, ...)`, so a student program that asks for too much memory fails instead of freezing the computer.

## Experiment 2: a private process list and no network

```text
sudo unshare --pid --fork --mount-proc --net bash
ps aux
ping -c 1 8.8.8.8
exit
```

**What I saw:**

```text
USER   PID  ...  COMMAND
root     1  ...  bash
root     7  ...  ps aux
```

and then:

```text
ping: connect: Network is unreachable
```

**What it means:** inside the new "box" the `bash` I started is process number 1, and `ps aux` shows only two processes (bash and `ps` itself). A normal Ubuntu shows hundreds. So `--pid --mount-proc` gives the program its **own private process list**: it cannot see or kill our other programs. `--net` gives it its **own empty network**, so `ping` fails with "Network is unreachable". Our runner starts every student program like this.

One more thing I learned: because the program is process number 1 inside the box, Linux ignores some kill signals for it. That is why our launcher starts the student program as a child process (see `docs/known-weaknesses.md`).

## Experiment 3: see what a program asks Linux to do

```text
strace -f -o /tmp/trace.txt python3 -c "print('hi')"
head -50 /tmp/trace.txt
```

**What I saw:** the program printed `hi`. The first 50 lines of the trace were lines like these:

```text
execve("/home/sree/codeexam-secure/.venv/bin/python3", ["python3", "-c", "print('hi')"], ...) = 0
brk(NULL)
mmap(NULL, 8192, PROT_READ|PROT_WRITE, ...)
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/usr/lib/x86_64-linux-gnu/libm.so.6", ...) = 3
openat(AT_FDCWD, "/usr/lib/x86_64-linux-gnu/libz.so.1", ...) = 3
openat(AT_FDCWD, "/usr/lib/x86_64-linux-gnu/libexpat.so.1", ...) = 3
openat(AT_FDCWD, "/usr/lib/x86_64-linux-gnu/libc.so.6", ...) = 3
read(3, ...)   mmap(...)   mprotect(...)   close(3)
```

**What it means:** even a one-line Python program makes many requests to Linux. Each request has a name, called a **system call** (`execve` starts a program, `openat` opens a file, `mmap` and `brk` get memory, `read` reads a file). The first 50 lines are only the program starting up and loading libraries. This also shows that `python3` here comes from our `.venv`.

The seccomp filter works on these names. Our filter will kill a program that uses a forbidden name such as `socket` or `connect`, and let all the normal names (`openat`, `read`, `write`, `mmap` and so on) through. If a normal program is ever killed by mistake, I can find the name with `strace` and remove it from the blocked list.

## Experiment 4: are control groups (cgroups) available?

```text
stat -fc %T /sys/fs/cgroup/
```

**What I saw:** `cgroup2fs`

**What it means:** cgroup version 2 is available on my WSL. Control groups can limit the memory of a whole group of processes, which is stronger than a limit per process. This means the stretch goal (cgroups, Task 8) can be tried on my machine. The prototype does not depend on it: it uses the simpler limits from Experiment 1.

## Summary for the team

| Building block | Tool | What it gives us |
|---|---|---|
| Limits | `ulimit` / `resource.setrlimit` | A program cannot use more memory, CPU time, processes or file size than we allow |
| Private view | `unshare --pid --fork --mount-proc --net` | A private process list and no network |
| Filter | seccomp (seen with `strace`) | A program that asks for a forbidden system call is killed |
| Control groups | cgroup v2 (`cgroup2fs` on my WSL) | Possible stretch goal: one memory limit for a whole group |