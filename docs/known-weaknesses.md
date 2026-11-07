# Known weaknesses of the prototype runner (honest list)

The prototype box is a **deliberate simplification** so a first-time team can finish. It is **not** a full defence. Say this clearly at the review.

1. **The C++ compile step is not filtered by seccomp.** It runs as the user `nobody` with limits, but compiler tricks (for example `#include "/some/readable/file"`) can leak files that `nobody` may read.
2. **Memory is limited per process (`RLIMIT_AS`), not per group.** A program that starts several processes can use more than the limit in total. Linux cgroups would fix this.
3. **`RLIMIT_AS` counts address space, not real memory.** Some languages need large address space to start (so we cannot set the limit very low).
4. **The process limit counts all processes of the user `nobody`.** If other programs run as `nobody`, the limit is shared with them.
5. **No limit on disk space** except the largest single file (`RLIMIT_FSIZE`). A program could write many small files in its scratch folder.
6. **The seccomp deny-list is short.** It blocks a list of dangerous calls and allows the rest. A deny-list can miss something; an allow-list is safer but takes longer to build and test.
7. **No CPU or timing isolation.** A program can measure time and may leak information through timing.
8. **The worker needs `sudo` without a password** (`scripts/setup_sudoers.sh`). This is a lab-only shortcut. A real system would use a separate privileged service.
9. **The kernel is shared.** A bug in Linux itself could let a program escape. Real systems add a stronger layer (for example gVisor or a micro virtual machine).
10. **Tested only on WSL2 Ubuntu 24.04.** Other kernels may behave differently.
11. **Signals and the private process list:** inside the private process list the program would be process number 1 and Linux ignores most signals for it. The launcher therefore runs the program as a child. If you change the launcher, keep this in mind.

## Stretch goal (cgroups): what to try, only after everything else works

```text
stat -fc %T /sys/fs/cgroup/                               # must say cgroup2fs
sudo mkdir /sys/fs/cgroup/codeexam
echo 268435456 | sudo tee /sys/fs/cgroup/codeexam/memory.max
```

If you see "No such file or directory" the memory controller is not enabled for this folder. Stop and write it down here. The simpler limits are enough for the prototype.

**What I tried and what happened:** _write here_
