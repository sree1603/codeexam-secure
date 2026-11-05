#include <iostream>
#include <string>
#include <stack>
using namespace std;

int main() {
    string text;
    getline(cin, text);

    stack<char> characters;

    for (char ch : text) {
        characters.push(ch);
    }

    while (!characters.empty()) {
        cout << characters.top();
        characters.pop();
    }

    cout << endl;
    return 0;
}
