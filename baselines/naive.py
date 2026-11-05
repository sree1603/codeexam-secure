import subprocess

def run_naive(command, stdin_text="", timeout_s=5):
    try:
        p = subprocess.run(
            command,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout_s
        )

        return {
            "stdout": p.stdout,
            "exit_code": p.returncode,
            "timed_out": False
        }

    except subprocess.TimeoutExpired as e:
        return {
            "stdout": (e.stdout or b"").decode()
            if isinstance(e.stdout, bytes)
            else (e.stdout or ""),
            "exit_code": None,
            "timed_out": True
        }
