# Memory attack 1: allocate memory in 100 MB steps up to 1.5 GB, then stop.
# Prints ATTACK_SUCCEEDED only if all 1.5 GB were really given to it.
chunks = []
for i in range(15):  # 15 x 100 MB = 1.5 GB, then stop
    chunks.append(bytearray(100 * 1024 * 1024))
print("ATTACK_SUCCEEDED")
