// CPU attack 2: busy loop for 8 seconds in C++ (bounded, stops by itself).
#include <chrono>
#include <iostream>

int main() {
    auto start = std::chrono::steady_clock::now();
    volatile unsigned long long x = 0;  // volatile so the compiler cannot remove the loop
    while (std::chrono::duration_cast<std::chrono::seconds>(
               std::chrono::steady_clock::now() - start).count() < 8) {
        x = x + 1;
    }
    std::cout << "ATTACK_SUCCEEDED" << std::endl;
    return 0;
}
