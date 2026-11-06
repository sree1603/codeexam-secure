import socket

try:
    c = socket.create_connection(("127.0.0.1", 9999), timeout=2)
    c.sendall(b"hello")
    print("ATTACK_SUCCEEDED")
    c.close()
except Exception:
    pass
