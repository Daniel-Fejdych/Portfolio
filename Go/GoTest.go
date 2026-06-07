// Package main is the entry point for the executable program.
package main

import (
	"fmt"
	"sync"
)

// worker is a function that runs as a goroutine.
// It reads numbers from the jobs channel, computes their square,
// and sends the result to the results channel.
// The `wg` WaitGroup is used to signal when all workers are done.
// Parameters:
//   - id: identifier for logging/debugging (helps track which worker processed a job)
//   - jobs: channel of integers to process (read-only)
//   - results: channel to send the squared results (write-only)
//   - wg: pointer to WaitGroup to mark completion when worker exits
func worker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	// Decrement the WaitGroup counter when the function returns.
	// This ensures that the main goroutine can wait for all workers to finish.
	defer wg.Done()

	// Loop over the jobs channel until it is closed and all values have been received.
	// The `range` loop automatically exits when the channel is closed.
	for num := range jobs {
		// Compute the square of the received number.
		square := num * num
		// Send the result into the results channel.
		// This operation blocks if the channel is full (not the case here, as it's unbuffered).
		results <- square
		// Optional: Print a log line to see which worker handled which job.
		fmt.Printf("Worker %d processed %d -> %d\n", id, num, square)
	}
}

// main is the entry point of the program.
func main() {
	// Define the list of numbers to process.
	numbers := []int{2, 4, 6, 8, 10, 12, 14, 16, 18, 20}

	// Number of workers in the pool. This controls the level of concurrency.
	numWorkers := 3

	// Create channels for jobs and results.
	// Both are unbuffered channels (buffer size 0), meaning sends and receives block until both sides are ready.
	// This is fine for work distribution because we will close the jobs channel after sending all jobs.
	jobs := make(chan int)
	results := make(chan int)

	// sync.WaitGroup is used to wait for all worker goroutines to finish.
	var wg sync.WaitGroup

	// Launch the worker goroutines.
	// Each worker starts and will wait for jobs to arrive on the `jobs` channel.
	for i := 1; i <= numWorkers; i++ {
		wg.Add(1) // Increment the WaitGroup counter for each worker.
		go worker(i, jobs, results, &wg)
	}

	// Send all numbers into the jobs channel.
	// This runs in a separate goroutine so that the sending does not block.
	// Once all numbers are sent, we close the jobs channel to signal workers that no more work will arrive.
	go func() {
		for _, num := range numbers {
			jobs <- num
		}
		close(jobs) // Closing the channel causes the workers' `range` loops to exit.
	}()

	// Another goroutine that waits for all workers to finish and then closes the results channel.
	// This allows the main goroutine to read results using `range` without deadlocking.
	go func() {
		wg.Wait()       // Wait for all workers to call `wg.Done()`.
		close(results)  // Closing results signals that no more results will be sent.
	}()

	// Collect and sum all results from the results channel.
	// The `range` loop will continue until `results` is closed and empty.
	totalSum := 0
	for square := range results {
		totalSum += square
	}

	// Print the final result.
	fmt.Printf("Sum of squares of %v is %d\n", numbers, totalSum)
}