"""WSL-only bounded attack: try up to 300 independent sleeping child processes."""
import subprocess
import sys


def main():
    children = []
    try:
        for _ in range(300):
            child = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(5)"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            children.append(child)
        print("ATTACK_SUCCEEDED", flush=True)
    except (OSError, RuntimeError):
        pass
    finally:
        for child in children:
            try:
                child.wait(timeout=6)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
