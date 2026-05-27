// totient_linear_seq.c
//
// Sequential Linear (Euler) Totient Sieve
// Computes sum of φ(n) for n in [1, N]

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

int main(int argc, char *argv[])
{
    /* Expected usage:
       ./totient_linear_seq N
    */
    if (argc != 2) {
        printf("Usage: %s start end\n", argv[0]);
        return 1;
    }

    int startRange = 1;
    int endRange   = atoi(argv[1]);

    if (startRange < 1 || endRange < startRange) {
        printf("Invalid range.\n");
        return 1;
    }

    int N = endRange;

    clock_t start = clock();

    /* Allocate arrays */
    int *phi = malloc((N + 1) * sizeof(int));
    int *primes = malloc((N + 1) * sizeof(int));
    char *isComposite = calloc(N + 1, sizeof(char));

    if (!phi || !primes || !isComposite) {
        printf("Memory allocation failed.\n");
        free(phi);
        free(primes);
        free(isComposite);
        return 1;
    }

    int primeCount = 0;

    /* Base case */
    phi[1] = 1;

    /* Linear sieve computation */
    for (int i = 2; i <= N; i++) {

        if (!isComposite[i]) {
            primes[primeCount++] = i;
            phi[i] = i - 1;
        }

        for (int j = 0; j < primeCount && (long long)i * primes[j] <= N; j++) {

            int p = primes[j];
            int ip = i * p;

            isComposite[ip] = 1;

            if (i % p == 0) {
                phi[ip] = phi[i] * p;
                break;
            } else {
                phi[ip] = phi[i] * (p - 1);
            }
        }
    }

    /* Sum only requested range */
    uint64_t sum = 0;
    for (int i = startRange; i <= endRange; i++)
        sum += phi[i];

    clock_t end = clock();

    printf("Sum: %llu\n", (unsigned long long)sum);
    printf("Runtime: %.6f seconds\n",
           (double)(end - start) / CLOCKS_PER_SEC);

    free(phi);
    free(primes);
    free(isComposite);

    return 0;
}