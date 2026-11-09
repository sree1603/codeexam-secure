# Attack programs (SAFETY WARNING)

These programs are **test attacks for our own lab**. They try to waste CPU, memory,
processes, network or read a protected file, so that we can measure whether our
locked box (the runner) stops them.

Rules:

1. Run them **only inside your own WSL Ubuntu**. Never on a shared or university server.
2. Never run them in GitHub Actions or any cloud service.
3. Every attack is **bounded**: it stops by itself (8 seconds of CPU, at most 1.5 GB of memory, a few processes).
4. An attack prints `ATTACK_SUCCEEDED` **only if it reached its goal**. If that line never
   appears, the attack was contained.
5. Do not make the attacks bigger. If something hangs, press `Ctrl+C` and run `pkill -f attacks/`.

Folders: `cpu/` and `memory/` (Varshita), `process/` (Hanson), `network/` and `files/` (Trisha).
