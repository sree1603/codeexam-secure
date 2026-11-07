# CPU attack 3: heavy maths loop for 8 seconds (bounded, stops by itself).
import math
import time

start = time.time()
total = 0.0
i = 1
while time.time() - start < 8:
    total += math.sqrt(i) * math.sin(i)  # real work, not just waiting
    i += 1
print("ATTACK_SUCCEEDED")
