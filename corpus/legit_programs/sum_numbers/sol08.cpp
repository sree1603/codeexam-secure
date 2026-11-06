#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;

    int total = 0;
    for (int i = 0; i < n; i++) {
        int number;
        cin >> number;
        total += number;
    }

    cout << total << endl;
    return 0;
}
