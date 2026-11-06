#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;

    int count = 0;

    for (int number = 2; number <= n; number++) {
        bool prime = true;
        int divisor = 2;

        while (divisor * divisor <= number) {
            if (number % divisor == 0) {
                prime = false;
                break;
            }
            divisor++;
        }

        if (prime) {
            count++;
        }
    }

    cout << count << endl;
    return 0;
}
