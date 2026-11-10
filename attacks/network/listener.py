import socket

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 9999))
server.listen(1)
server.settimeout(30)

try:
    connection, _ = server.accept()
    print("GOT_CONNECTION")
    connection.close()
except socket.timeout:
    print("NO_CONNECTION")
finally:
    server.close()
