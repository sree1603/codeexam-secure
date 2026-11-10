import pytest

from judge.verdict import VERDICTS, decide_test, normalize, overall_verdict


def runner_result(**overrides):
    return {"id": "1", "stdout": "5\n", "exit_code": 0, "violation": None, **overrides}


@pytest.mark.parametrize("compile_info,result,expected,verdict", [
    ({"ok": True}, runner_result(), "5\n", "accepted"),
    ({"ok": True}, runner_result(stdout="6\n"), "5\n", "wrong_answer"),
    ({"ok": False}, runner_result(), "5\n", "compile_error"),
    ({"ok": True}, runner_result(exit_code=1), "5\n", "runtime_error"),
    ({"ok": True}, runner_result(violation="time_limit"), "5\n", "time_limit"),
    ({"ok": True}, runner_result(violation="memory_limit"), "5\n", "memory_limit"),
    ({"ok": True}, runner_result(violation="output_limit"), "5\n", "output_limit"),
    ({"ok": True}, runner_result(violation="forbidden_call"), "5\n", "policy_violation"),
    ({"ok": True}, runner_result(violation="network_blocked"), "5\n", "policy_violation"),
    ({"ok": True}, runner_result(violation="process_limit"), "5\n", "policy_violation"),
])
def test_each_runner_verdict(compile_info, result, expected, verdict):
    assert decide_test(compile_info, result, expected) == verdict


def test_all_nine_verdict_names():
    assert set(VERDICTS) == {"accepted", "wrong_answer", "compile_error", "runtime_error",
                            "time_limit", "memory_limit", "output_limit", "policy_violation",
                            "internal_error"}
    assert overall_verdict(["accepted", "wrong_answer", "time_limit"]) == "wrong_answer"
    assert overall_verdict(["accepted", "accepted"]) == "accepted"
    assert overall_verdict(["internal_error"]) == "internal_error"


def test_output_normalization_only_trailing_whitespace():
    assert normalize("5  \n\n") == "5"
    assert normalize("1 2\n") != normalize("12\n")
