#!/usr/bin/env bash
FAILED=0
ok()  { echo "PASS: $1"; }
bad() { echo "FAIL: $1"; FAILED=1; }

case "$PWD" in /mnt/*) bad "project is inside /mnt (move it to your Linux home folder)";; *) ok "project is in the Linux folder";; esac
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' && ok "python 3.11 or newer" || bad "python 3.11 or newer"
command -v g++ >/dev/null && ok "g++ compiler" || bad "g++ compiler"
command -v git >/dev/null && ok "git" || bad "git"
command -v unshare >/dev/null && ok "unshare" || bad "unshare"
python3 -c 'import seccomp' 2>/dev/null && ok "python seccomp library" || bad "python seccomp library"
if [ "$(stat -fc %T /sys/fs/cgroup/)" = "cgroup2fs" ]; then ok "cgroup v2 present"; else echo "WARN: cgroup v2 not found (the prototype uses simpler limits)"; fi
exit $FAILED