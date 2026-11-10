// WSL-only bounded attack: try forking 300 children that each sleep 5 seconds.
#include <cerrno>
#include <cstdio>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

int main() {
    std::vector<pid_t> children;
    bool all_started = true;
    for (int i = 0; i < 300; ++i) {
        pid_t pid = fork();
        if (pid == 0) {
            sleep(5);
            _exit(0);
        }
        if (pid < 0) {
            all_started = false;
            break;
        }
        children.push_back(pid);
    }
    if (all_started) {
        puts("ATTACK_SUCCEEDED");
        fflush(stdout);
    }
    for (pid_t pid : children) {
        waitpid(pid, nullptr, 0);
    }
    return 0;
}
