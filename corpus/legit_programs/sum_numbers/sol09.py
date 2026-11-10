n = int(input())

numbers = list(map(int, input().split()))

total = 0

i = 0
while i < len(numbers):
    total = total + numbers[i]
    i += 1

print(total)
