import math

n = int(input())

count = 0

for number in range(2, n + 1):
    prime = True

    for i in range(2, math.isqrt(number) + 1):
        if number % i == 0:
            prime = False
            break

    if prime:
        count += 1

print(count)
