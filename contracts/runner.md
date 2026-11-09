# Runner contract (the message between the worker and the runner)

Owner: Varshita (Person 1). Reviewer: Hanson. **Do not change this format without a GitHub issue that all three of us agree on.**

The worker calls the runner like this (the runner needs root, so the worker uses `sudo`):

```text
sudo -n .venv/bin/python -m runner.run_cli request.json
```

The runner prints the RESPONSE as JSON on standard output.

## REQUEST

```json
{
  "submission_id": "s-0042",
  "language": "python",
  "source": "n = int(input())\nprint(n * 2)\n",
  "limits": {"cpu_ms": 2000, "wall_ms": 5000, "memory_mb": 256, "processes": 8, "output_kb": 1024},
  "tests": [{"id": "t1", "stdin": "3\n"}]
}
```

- `language` is `"python"` or `"cpp"`.
- `limits` is optional. Missing values use the defaults shown above.
- `cpu_ms` is CPU time, `wall_ms` is the clock time, `memory_mb` is the memory, `processes` is the number of processes and threads, `output_kb` is the largest output.

## RESPONSE

```json
{
  "submission_id": "s-0042",
  "compile": {"ok": true, "message": ""},
  "results": [
    {"id": "t1", "stdout": "6\n", "cpu_ms": 18, "wall_ms": 31, "peak_kb": 9120,
     "exit_code": 0, "violation": null}
  ]
}
```

- `compile.ok` is `false` when a C++ program does not compile. Then `message` holds the first 2000 characters of the compiler message and `results` is an empty list. Python programs have no compile step (`ok` is always `true`).
- `exit_code` is the program's exit code. If the program was killed by a signal it is the **negative** signal number (for example `-31` for SIGSYS, `-24` for SIGXCPU).
- `violation` is `null` or one of the texts below.

## Allowed violation texts

| violation | Meaning | Hanson maps it to the verdict |
|---|---|---|
| `time_limit` | too much CPU time or clock time | `time_limit` |
| `memory_limit` | asked for more memory than allowed (or killed by the kernel for memory) | `memory_limit` |
| `output_limit` | wrote more output than `output_kb` | `output_limit` |
| `process_limit` | tried to start too many processes or threads | `policy_violation` |
| `forbidden_call` | the seccomp filter killed the program (for example it asked for a network socket) | `policy_violation` |
| `network_blocked` | a network call failed because there is no network | `policy_violation` |
| `launcher_error` | the box could not start safely (for example the seccomp library is missing) | `internal_error` |

If `violation` is `null`, Hanson decides between `accepted`, `wrong_answer` and `runtime_error` from `exit_code` and the output. The compile result gives `compile_error`.

## Error response

If the runner itself breaks it prints `{"submission_id": "...", "error": "internal_error: <text>"}` and exits with code 1. The worker must use the verdict `internal_error` and keep the submission for a retry.

## Verdict names (exactly these)

`accepted`, `wrong_answer`, `compile_error`, `runtime_error`, `time_limit`, `memory_limit`, `output_limit`, `policy_violation`, `internal_error`
