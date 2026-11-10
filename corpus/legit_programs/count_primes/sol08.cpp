#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;

    vector<bool> prime(n + 1, true);

    if (n >= 0) prime[0] = false;
    if (n >= 1) prime[1] = false;

    for (int i = 2; i * i <= n; i++) {
        if (prime[i]) {
            for (int j = i * i; j <= n; j += i) {
                prime[j] = false;
            }
        }
    }

    int count = 0;

    for (int i = 2; i <= n; i++) {
        if (prime[i]) {
            count++;
        }
    }

    cout << count << endl;
    return 0;
}
