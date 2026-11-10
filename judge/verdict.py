"""Verdict decisions follow the team's published contract verbatim."""

VERDICTS = (
    "accepted", "wrong_answer", "compile_error", "runtime_error", "time_limit",
    "memory_limit", "output_limit", "policy_violation", "internal_error",
)


def normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def decide_test(compile_info: dict, result: dict, expected: str) -> str:
    if not compile_info["ok"]:
        return "compile_error"
    violation = result.get("violation")
    if violation in ("forbidden_call", "network_blocked", "process_limit"):
        return "policy_violation"
    if violation in ("time_limit", "memory_limit", "output_limit"):
        return violation
    if result["exit_code"] != 0:
        return "runtime_error"
    if normalize(result["stdout"]) != normalize(expected):
        return "wrong_answer"
    return "accepted"


def overall_verdict(test_verdicts: list[str]) -> str:
    return next((v for v in test_verdicts if v != "accepted"), "accepted")
