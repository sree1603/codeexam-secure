# CodeExam Secure

A prototype that runs student code safely during programming exams and grades it with a tamper-evident log.

## Setup (Windows with WSL2 Ubuntu)

1. Install WSL and Ubuntu, then clone this repo into `~/codeexam-secure` (not under `/mnt/c`).
2. Run `bash scripts/check_env.sh` and make sure every line says PASS.

## Run

    make setup     # create the virtual environment and install libraries
    make test      # run all tests
    make run       # start the web server
    make worker    # start the grading worker (second terminal)

## Safety rule

The programs in `attacks/` are test attacks for our own lab. Run them only inside your own WSL Ubuntu, never on a shared server.
