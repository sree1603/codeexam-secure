n = int(input())

count = 0

for number in range(2, n + 1):
    if all(number % divisor != 0
           for divisor in range(2, int(number ** 0.5) + 1)):
        count += 1

print(count)
