"""Command line for the runner: reads a REQUEST json file, prints the RESPONSE json.

Owner: Varshita (Person 1).  Task 6 of the guide.

    sudo .venv/bin/python -m runner.run_cli examples/request1.json
    sudo .venv/bin/python -m runner.run_cli -          # read the request from standard input

Exit code 0 = a response was printed. Exit code 1 = internal error; the printed json
then has an "error" text and the worker should use the verdict internal_error.
"""
import json
import os
import sys

from runner.sandbox import can_isolate, run_request


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: python -m runner.run_cli request.json\n")
        return 2
    request = {}
    try:
        text = sys.stdin.read() if argv[1] == "-" else open(argv[1], encoding="utf-8").read()
        request = json.loads(text)
        if not can_isolate():
            sys.stderr.write("WARNING: not running as root, so there is NO private view "
                             "and NO safe user. Use sudo for real isolation.\n")
        response = run_request(request)
        print(json.dumps(response))
        return 0
    except Exception as error:  # noqa: BLE001
        print(json.dumps({"submission_id": request.get("submission_id") if isinstance(request, dict) else None,
                          "error": "internal_error: %s" % error}))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
