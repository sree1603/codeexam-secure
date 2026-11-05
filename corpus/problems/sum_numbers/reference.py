n = int(input())

if n == 0:
    print(0)
else:
    numbers = list(map(int, input().split()))
    print(sum(numbers))
