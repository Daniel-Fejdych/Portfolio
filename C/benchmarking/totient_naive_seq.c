// totient_naive_seq.c
// Sequential naive totient summation over a range:
// Usage: ./totient_naive_seq N

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

static inline uint64_t phi_naive(uint64_t n)
{
    uint64_t result = n;

    /* Handle factor 2 separately */
    if ((n & 1ULL) == 0) {
        result -= result >> 1;
        while ((n & 1ULL) == 0)
            n >>= 1;
    }

    /* Check odd factors up to sqrt(n) */
    for (uint64_t i = 3; i * i <= n; i += 2) {
        if (n % i == 0) {
            result -= result / i;
            while (n % i == 0)
                n /= i;
        }
    }

    /* If remaining n is prime */
    if (n > 1)
        result -= result / n;

    return result;
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        printf("Usage: %s N\n", argv[0]);
        return 1;
    }

    uint64_t startRange = 1;
    uint64_t endRange   = strtoull(argv[1], NULL, 10);

    if (startRange < 1 || endRange < startRange) {
        printf("Invalid range.\n");
        return 1;
    }

    clock_t start_time = clock();

    uint64_t sum = 0;

    for (uint64_t i = startRange; i <= endRange; i++)
        sum += phi_naive(i);

    clock_t end_time = clock();

    double runtime =
        (double)(end_time - start_time) / CLOCKS_PER_SEC;

    printf("Sum: %llu\n", (unsigned long long)sum);
    printf("Runtime: %.6f seconds\n", runtime);

    return 0;
}