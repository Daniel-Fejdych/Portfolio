import math
import time

def sm(num):
    for prime in primes[0:(math.isqrt(num))]:
        if (num % prime == 0): return
    primes.append(num)

primes = [2, 3]

t0 = time.time()
for i in range(1, 100000):
    sm(6 * i - 1)
    sm(6 * i + 1)
t1 = time.time()
print("Time required:", t1 - t0)
print(primes)
t2 = time.time()
print("Time required:", t2 - t1)
