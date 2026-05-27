// totient_linear_omp.c
//
// Usage:
//   ./totient_linear_omp numThreads N
//
// Parallelises only the summation phase.
// Prime generation remains sequential due to data dependencies.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <omp.h>

int main(int argc, char *argv[])
{
    if (argc != 3) {
        printf("Usage: %s numThreads N\n", argv[0]);
        return 1;
    }

    int threads   = atoi(argv[1]);
    int chunkSize = 4;
    int N         = atoi(argv[2]);

    if (threads <= 0 || chunkSize <= 0 || N <= 0) {
        printf("Error: All inputs must be positive integers.\n");
        return 1;
    }

    omp_set_num_threads(threads);

    double start = omp_get_wtime();

    /* Allocate memory */
    int *phi = malloc((N + 1) * sizeof(int));
    int *primes = malloc((N + 1) * sizeof(int));
    char *isComposite = calloc(N + 1, sizeof(char));

    if (!phi || !primes || !isComposite) {
        printf("Memory allocation failed.\n");
        return 1;
    }

    int primeCount = 0;
    phi[1] = 1;

    /* -------------------------------
       Sequential Linear Sieve Phase
       ------------------------------- */
    for (int i = 2; i <= N; i++) {

        if (!isComposite[i]) {
            primes[primeCount++] = i;
            phi[i] = i - 1;
        }

        for (int j = 0; j < primeCount && i * primes[j] <= N; j++) {
            int p = primes[j];
            isComposite[i * p] = 1;

            if (i % p == 0) {
                phi[i * p] = phi[i] * p;
                break;
            } else {
                phi[i * p] = phi[i] * (p - 1);
            }
        }
    }

    /* -------------------------------
       Parallel Summation Phase
       ------------------------------- */
    uint64_t sum = 0;

    #pragma omp parallel for reduction(+:sum) schedule(dynamic, chunkSize)
    for (int i = 1; i <= N; i++) {
        sum += phi[i];
    }

    double end = omp_get_wtime();

    printf("Sum: %llu\n", (unsigned long long)sum);
    printf("Runtime: %.6f seconds\n", end - start);

    free(phi);
    free(primes);
    free(isComposite);

    return 0;
}