// totient_naive_omp.c
// Usage:
//     ./totient_naive_omp numThreads N

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <omp.h>

/* 
 * Optimized naive Euler totient using trial division.
 * Fully independent computation per n.
 */
static inline uint64_t phi_naive(uint64_t n)
{
    uint64_t result = n;

    /* Handle factor 2 */
    if ((n & 1) == 0) {
        result -= result >> 1;
        while ((n & 1) == 0)
            n >>= 1;
    }

    /* Check odd factors */
    for (uint64_t i = 3; i * i <= n; i += 2) {
        if (n % i == 0) {
            result -= result / i;
            while (n % i == 0)
                n /= i;
        }
    }

    /* If remainder is prime */
    if (n > 1)
        result -= result / n;

    return result;
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        printf("Usage: %s numThreads startRange endRange\n", argv[0]);
        return 1;
    }

    int numThreads = atoi(argv[1]);
    uint64_t startR = 1;
    uint64_t endR   = strtoull(argv[2], NULL, 10);

    if (numThreads <= 0 || startR > endR) {
        printf("Invalid arguments.\n");
        return 1;
    }

    omp_set_num_threads(numThreads);

    double start_time = omp_get_wtime();

    uint64_t sum = 0;

    #pragma omp parallel for schedule(dynamic, 64) reduction(+:sum)
    for (uint64_t i = startR; i <= endR; i++) {
        sum += phi_naive(i);
    }

    double end_time = omp_get_wtime();

    printf("Sum: %llu\n", (unsigned long long)sum);
    printf("Runtime: %.6f seconds\n", end_time - start_time);

    return 0;
}