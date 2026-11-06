n = int(input())

values = [int(x) for x in input().split()]

answer = sum(values[:n])

print(answer)
