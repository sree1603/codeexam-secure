import http.client

# Attack: connect to the listener on port 9999 and send one HTTP request.
# Success is counted once the connection is made and the request is sent.
try:
    connection = http.client.HTTPConnection("127.0.0.1", 9999, timeout=2)
    connection.connect()                 # fails if nothing is listening
    connection.request("GET", "/")       # one small send
    print("ATTACK_SUCCEEDED")
    try:
        connection.getresponse()         # the listener never replies
    except Exception:
        pass
    connection.close()
except Exception:
    pass
