#!/bin/bash

###############################################################################
# Totient Benchmark Suite (No bc Required)
#
# - Runs 5 repetitions per configuration
# - Benchmarks:
#     * Naive (Sequential + OpenMP)
#     * Classic Sieve (Sequential + OpenMP)
#     * Linear Sieve (Sequential + OpenMP)
# - Computes:
#     * Average runtime
#     * Speedup
#     * Parallel efficiency
#     * Throughput (N / runtime)
# - Outputs results to CSV
###############################################################################

##############################
# Configuration
##############################

THREADS=(1 2 4 8 12 16 20 24 28 32 36 40 44 48 52 56 60 64)
RANGES=(15000 30000 100000)
RUNS=5

NAIVE_SEQ=./totient_naive_seq
NAIVE_OMP=./totient_naive_omp
SIEVE_SEQ=./totient_sieve_seq
SIEVE_OMP=./totient_sieve_omp
LINEAR_SEQ=./totient_linear_seq
LINEAR_OMP=./totient_linear_omp

OUTPUT_FILE="totient_benchmark_results.csv"

##############################
# Validation
##############################

echo "Validating executables..."

for exe in $NAIVE_SEQ $NAIVE_OMP $SIEVE_SEQ $SIEVE_OMP $LINEAR_SEQ $LINEAR_OMP; do
    if [ ! -x "$exe" ]; then
        echo "ERROR: Executable $exe not found or not executable."
        exit 1
    fi
done

echo "Environment OK."
echo "Writing results to $OUTPUT_FILE"

##############################
# Helper Functions
##############################

# Extract runtime from program output
extract_runtime() {
    grep "Runtime:" | awk '{print $2}'
}

# Run command RUNS times and compute average
average_runs() {
    local total=0
    for ((i=1; i<=RUNS; i++)); do
        runtime=$($@ | extract_runtime)

        if [ -z "$runtime" ]; then
            echo "ERROR: Failed to extract runtime."
            exit 1
        fi

        total=$(awk -v a="$total" -v b="$runtime" 'BEGIN { printf "%.10f", a+b }')
    done

    awk -v sum="$total" -v r="$RUNS" 'BEGIN { printf "%.10f", sum/r }'
}

##############################
# CSV Header
##############################

echo "Range,Algorithm,Threads,AverageRuntime,Speedup,Efficiency,Throughput" > "$OUTPUT_FILE"

##############################
# Benchmark Execution
##############################

for N in "${RANGES[@]}"; do

    echo "Processing range 1 to $N ..."

    ############################################################
    # Sequential Baselines
    ############################################################

    naive_seq_avg=$(average_runs $NAIVE_SEQ $N)
    sieve_seq_avg=$(average_runs $SIEVE_SEQ $N)
    linear_seq_avg=$(average_runs $LINEAR_SEQ $N)

    # Write sequential entries (speedup = 1, efficiency = 1)
    echo "$N,Naive_Seq,1,$naive_seq_avg,1.0,1.0,$(awk -v n="$N" -v t="$naive_seq_avg" 'BEGIN { printf "%.10f", n/t }')" >> "$OUTPUT_FILE"
    echo "$N,Sieve_Seq,1,$sieve_seq_avg,1.0,1.0,$(awk -v n="$N" -v t="$sieve_seq_avg" 'BEGIN { printf "%.10f", n/t }')" >> "$OUTPUT_FILE"
    echo "$N,Linear_Seq,1,$linear_seq_avg,1.0,1.0,$(awk -v n="$N" -v t="$linear_seq_avg" 'BEGIN { printf "%.10f", n/t }')" >> "$OUTPUT_FILE"

    ############################################################
    # Parallel Naive
    ############################################################

    for t in "${THREADS[@]}"; do
        avg=$(average_runs $NAIVE_OMP $t $N)

        speedup=$(awk -v s="$naive_seq_avg" -v p="$avg" 'BEGIN { printf "%.10f", s/p }')
        efficiency=$(awk -v sp="$speedup" -v th="$t" 'BEGIN { printf "%.10f", sp/th }')
        throughput=$(awk -v n="$N" -v rt="$avg" 'BEGIN { printf "%.10f", n/rt }')

        echo "$N,Naive_OMP,$t,$avg,$speedup,$efficiency,$throughput" >> "$OUTPUT_FILE"
    done

    ############################################################
    # Parallel Classic Sieve
    ############################################################

    for t in "${THREADS[@]}"; do
        avg=$(average_runs $SIEVE_OMP $t $N)

        speedup=$(awk -v s="$sieve_seq_avg" -v p="$avg" 'BEGIN { printf "%.10f", s/p }')
        efficiency=$(awk -v sp="$speedup" -v th="$t" 'BEGIN { printf "%.10f", sp/th }')
        throughput=$(awk -v n="$N" -v rt="$avg" 'BEGIN { printf "%.10f", n/rt }')

        echo "$N,Sieve_OMP,$t,$avg,$speedup,$efficiency,$throughput" >> "$OUTPUT_FILE"
    done

    ############################################################
    # Parallel Linear Sieve
    ############################################################

    for t in "${THREADS[@]}"; do
        avg=$(average_runs $LINEAR_OMP $t $N)

        speedup=$(awk -v s="$linear_seq_avg" -v p="$avg" 'BEGIN { printf "%.10f", s/p }')
        efficiency=$(awk -v sp="$speedup" -v th="$t" 'BEGIN { printf "%.10f", sp/th }')
        throughput=$(awk -v n="$N" -v rt="$avg" 'BEGIN { printf "%.10f", n/rt }')

        echo "$N,Linear_OMP,$t,$avg,$speedup,$efficiency,$throughput" >> "$OUTPUT_FILE"
    done

done

echo "Benchmark complete."
echo "Results saved to $OUTPUT_FILE"