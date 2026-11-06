#include <iostream>
using namespace std;

bool isPrime(int number) {
    if (number < 2) {
        return false;
    }

    for (int i = 2; i * i <= number; i++) {
        if (number % i == 0) {
            return false;
        }
    }

    return true;
}

int main() {
    int n;
    cin >> n;

    int count = 0;

    for (int number = 2; number <= n; number++) {
        if (isPrime(number)) {
            count++;
        }
    }

    cout << count << endl;

    return 0;
}
