n = int(input())

is_prime = [True] * (n + 1)

if n >= 0:
    is_prime[0] = False

if n >= 1:
    is_prime[1] = False

for number in range(2, int(n ** 0.5) + 1):
    if is_prime[number]:
        for multiple in range(number * number, n + 1, number):
            is_prime[multiple] = False

print(sum(is_prime))
