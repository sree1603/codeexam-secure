n = int(input())

numbers = list(map(int, input().split()))

i = 0
total = 0

while i < n:
    total += numbers[i]
    i += 1

print(total)
