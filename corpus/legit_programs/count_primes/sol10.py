n = int(input())

primes = []

for number in range(2, n + 1):
    prime = True

    for divisor in primes:
        if divisor * divisor > number:
            break

        if number % divisor == 0:
            prime = False
            break

    if prime:
        primes.append(number)

print(len(primes))
