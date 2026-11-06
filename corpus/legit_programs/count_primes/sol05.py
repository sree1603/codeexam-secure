n = int(input())

count = 0
number = 2

while number <= n:
    prime = True
    divisor = 2

    while divisor * divisor <= number:
        if number % divisor == 0:
            prime = False
            break

        divisor += 1

    if prime:
        count += 1

    number += 1

print(count)
