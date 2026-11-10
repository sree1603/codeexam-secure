#include <iostream>
#include <string>
#include <algorithm>
using namespace std;

int main() {
    string text;
    getline(cin, text);

    reverse(text.begin(), text.end());

    cout << text << endl;

    return 0;
}
