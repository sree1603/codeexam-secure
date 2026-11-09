# Memory attack 3: ask for ONE 1.5 GB block (bounded, one allocation only).
block = bytearray(1500 * 1024 * 1024)
block[-1] = 1  # touch the end so it is really used
print("ATTACK_SUCCEEDED")
