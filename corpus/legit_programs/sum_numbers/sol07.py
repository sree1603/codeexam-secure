n = int(input())

numbers = map(int, input().split())

total = 0
count = 0

for number in numbers:
    total += number
    count += 1

print(total)
