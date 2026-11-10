"""WSL-only bounded attack: try 300 parallel forked sleepers."""
import os
import time


def main():
    children = []
    try:
        for _ in range(300):
            pid = os.fork()
            if pid == 0:
                time.sleep(5)
                os._exit(0)
            children.append(pid)
        print("ATTACK_SUCCEEDED", flush=True)
    except OSError:
        pass
    finally:
        for pid in children:
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass


if __name__ == "__main__":
    main()
