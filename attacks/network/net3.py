import urllib.request

try:
    request = urllib.request.Request(
        "http://127.0.0.1:9999/",
        data=b"hello",
        method="POST"
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        print("ATTACK_SUCCEEDED")
except Exception:
    pass
