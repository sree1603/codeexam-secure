def is_prime(num):
    if num < 2:
        return False

    for i in range(2, int(num ** 0.5) + 1):
        if num % i == 0:
            return False

    return True


n = int(input())

count = 0
for number in range(2, n + 1):
    if is_prime(number):
        count += 1

print(count)
