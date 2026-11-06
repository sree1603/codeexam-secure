#include <iostream>
#include <cstring>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);

    if (sock < 0) {
        return 0;
    }

    sockaddr_in server{};
    server.sin_family = AF_INET;
    server.sin_port = htons(9999);
    inet_pton(AF_INET, "127.0.0.1", &server.sin_addr);

    if (connect(sock, (struct sockaddr*)&server, sizeof(server)) == 0) {
        send(sock, "hello", 5, 0);
        std::cout << "ATTACK_SUCCEEDED" << std::endl;
    }

    close(sock);
    return 0;
}
