import sys

data = list(map(int, sys.stdin.read().split()))

n = data[0]
numbers = data[1:n + 1]

result = 0
for num in numbers:
    result = result + num

print(result)
