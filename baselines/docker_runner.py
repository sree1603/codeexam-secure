import subprocess

def run_docker(program_dir, program_name, timeout_s=10):
    command = [
        "docker", "run", "--rm",
        "--memory=256m",
        "-v", f"{program_dir}:/work:ro",
        "python:3.12-slim",
        "python", f"/work/{program_name}"
    ]

    p = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_s
    )

    return {
        "stdout": p.stdout,
        "exit_code": p.returncode,
        "timed_out": False
    }
