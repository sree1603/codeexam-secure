// Memory attack 2: allocate 1.5 GB in 100 MB steps in C++ and WRITE to it,
// so the memory is really used. Bounded: stops after 15 steps.
#include <cstring>
#include <iostream>
#include <vector>

int main() {
    std::vector<char*> blocks;
    for (int i = 0; i < 15; i++) {
        char* p = new char[100 * 1024 * 1024];  // throws std::bad_alloc if refused
        std::memset(p, 1, 100 * 1024 * 1024);   // touch every byte
        blocks.push_back(p);
    }
    std::cout << "ATTACK_SUCCEEDED" << std::endl;
    for (char* p : blocks) delete[] p;
    return 0;
}
