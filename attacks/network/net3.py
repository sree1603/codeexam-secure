import socket

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(b"hello", ("127.0.0.1", 9999))
    print("ATTACK_SUCCEEDED")
    s.close()
except Exception:
    pass
