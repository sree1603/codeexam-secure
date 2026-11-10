# Attack table

Each row is one attack program. **CONTAINED** means the attack did not print `ATTACK_SUCCEEDED`. **NOT_CONTAINED** means the attack reached its goal.

| attack | category | naive | docker | ours |
|---|---|---|---|---|
| cpu1.py | cpu | NOT_CONTAINED | NOT_CONTAINED | CONTAINED |
| cpu2.cpp | cpu | NOT_CONTAINED | NOT_CONTAINED | CONTAINED |
| cpu3.py | cpu | NOT_CONTAINED | NOT_CONTAINED | CONTAINED |
| mem1.py | memory | NOT_CONTAINED | CONTAINED | CONTAINED |
| mem2.cpp | memory | NOT_CONTAINED | CONTAINED | CONTAINED |
| mem3.py | memory | NOT_CONTAINED | CONTAINED | CONTAINED |
| file1.py | files | NOT_CONTAINED | CONTAINED | CONTAINED |
| file2.cpp | files | NOT_CONTAINED | CONTAINED | CONTAINED |
| file3.py | files | NOT_CONTAINED | CONTAINED | CONTAINED |

## Reading the table

- **naive** contained 0 of 9 attacks.
  - not contained: cpu1.py, cpu2.cpp, cpu3.py, mem1.py, mem2.cpp, mem3.py, file1.py, file2.cpp, file3.py
- **docker** contained 6 of 9 attacks.
  - not contained: cpu1.py, cpu2.cpp, cpu3.py
- **ours** contained 9 of 9 attacks.

Stability: the table was identical in all 3 runs.

