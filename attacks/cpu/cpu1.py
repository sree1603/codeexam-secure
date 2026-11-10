# CPU attack 1: busy loop for 8 seconds (bounded, stops by itself).
# Prints ATTACK_SUCCEEDED only if it was allowed to run the full 8 seconds.
import time

start = time.time()
while time.time() - start < 8:  # waste CPU time
    pass
print("ATTACK_SUCCEEDED")
