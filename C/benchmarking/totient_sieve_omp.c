// totient_sieve_omp.c

#include <stdio.h>
#include <stdlib.h>
#include <omp.h>


int main(int argc, char *argv[])
{
    /*
     * Usage:
     *   ./totient_sieve_omp threads N
     *
     * Computes:
     *   sum φ(1..N)
     */

    if (argc != 3) {
        printf("Usage: %s threads N\n", argv[0]);
        return 1;
    }

    int requestedThreads = atoi(argv[1]);
    int N = atoi(argv[2]);

    if (N <= 0) {
        printf("N must be above 1\n");
        return 1;
    }
    int chunk;

    omp_set_num_threads(requestedThreads);

    /* Automatic chunk estimation */
    chunk = N / (requestedThreads * 4);

    long long sum = 0;

    int *phi = malloc((N + 1) * sizeof(int));
    if (!phi) {
        printf("Memory allocation failed\n");
        return 1;
    }

    double start = omp_get_wtime();

    /* ---- Initialization ---- */
    #pragma omp parallel for schedule(static, chunk)
    for (int i = 0; i <= N; i++)
        phi[i] = i;

    /* ---- Totient Sieve ---- */
    for (int p = 2; p <= N; p++) {
        if (phi[p] == p) {   // p is prime
            //#pragma omp parallel for schedule(dynamic, chunk) //too slow
            for (int j = p; j <= N; j += p)
                phi[j] -= phi[j] / p;
        }
    }

    /* ---- Parallel Summation ---- */
    #pragma omp parallel for reduction(+:sum) schedule(static, chunk)
    for (int i = 1; i <= N; i++)
        sum += phi[i];

    double end = omp_get_wtime();

    /* Required format for benchmark script */
    printf("Sum: %lld\n", sum);
    printf("Runtime: %.6f seconds\n", end - start);

    free(phi);
    return 0;
}