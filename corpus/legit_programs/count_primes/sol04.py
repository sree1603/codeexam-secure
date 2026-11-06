def is_prime(number):
    if number < 2:
        return False

    for divisor in range(2, int(number ** 0.5) + 1):
        if number % divisor == 0:
            return False

    return True


n = int(input())

count = 0

for number in range(1, n + 1):
    if is_prime(number):
        count += 1

print(count)
