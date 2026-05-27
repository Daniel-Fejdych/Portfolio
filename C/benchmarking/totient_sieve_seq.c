// totient_sieve_seq.c

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

/*
 * Fast sequential totient summation
 * Computes sum φ(startR..endR)
 *
 * Usage:
 *   ./totient_sieve_seq N
 */

int main(int argc, char *argv[])
{
    if (argc != 2) {
        printf("Usage: %s startR endR\n", argv[0]);
        return 1;
    }

    int startR = 1;
    int endR   = atoi(argv[1]);

    if (startR < 1 || endR < startR) {
        printf("Invalid range. Must satisfy 1 <= startR <= endR\n");
        return 1;
    }

    /* Allocate φ array up to endR */
    int * restrict phi = malloc((endR + 1) * sizeof(int));
    if (!phi) {
        printf("Memory allocation failed\n");
        return 1;
    }

    clock_t start = clock();

    /* Initialize φ[i] = i */
    for (int i = 0; i <= endR; i++)
        phi[i] = i;

    /* Totient sieve (classic O(N log log N)) */
    for (int p = 2; p <= endR; p++) {
        if (phi[p] == p) {  // p is prime
            for (int j = p; j <= endR; j += p)
                phi[j] -= phi[j] / p;
        }
    }

    /* Sum only the requested range */
    uint64_t sum = 0;
    for (int i = startR; i <= endR; i++)
        sum += phi[i];

    clock_t end = clock();
    double runtime = (double)(end - start) / CLOCKS_PER_SEC;

    printf("Sum: %llu\n", (unsigned long long)sum);
    printf("Runtime: %.6f seconds\n", runtime);

    free(phi);
    return 0;
}