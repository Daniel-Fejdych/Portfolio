#include <iostream>

using namespace std;

/*
    Function: isPrime

    Purpose:
    Checks whether a given number is prime.

    Parameters:
    number - the integer we want to test.

    Returns:
    true  -> if the number is prime
    false -> if the number is not prime
*/
bool isPrime(int number)
{
    // Numbers less than 2 are not prime.
    // Prime numbers start at 2.
    if (number < 2)
    {
        return false;
    }

    // Check whether any number from 2 up to
    // the square root of the number divides it.
    // Using i * i <= number avoids needing <cmath>.
    for (int i = 2; i * i <= number; i++)
    {
        // If there is no remainder, then
        // the number has a divisor and is not prime.
        if (number % i == 0)
        {
            return false;
        }
    }

    // If no divisors were found,
    // the number is prime.
    return true;
}

int main()
{
    // Variable that stores which prime number
    // the user wants.
    int n;

    // Ask the user for input.
    cout << "Enter n: ";

    // Read the input from the keyboard.
    cin >> n;

    // Validate the input.
    // There is no 0th or negative prime number.
    if (n <= 0)
    {
        cout << "n must be a positive integer." << endl;
        return 1;
    }

    // This variable counts how many prime
    // numbers we have found so far.
    int primeCount = 0;

    // This variable will store the current
    // number we are testing.
    int currentNumber = 1;

    // This variable will eventually store
    // the answer (the n-th prime).
    int nthPrime = 0;

    // Continue searching until we have found
    // exactly n prime numbers.
    while (primeCount < n)
    {
        // Move to the next number.
        currentNumber++;

        // Check whether the current number is prime.
        if (isPrime(currentNumber))
        {
            // Increase the count of primes found.
            primeCount++;

            // Save this prime number.
            nthPrime = currentNumber;
        }
    }

    // Display the result.
    cout << "The " << n << "th prime number is: "
         << nthPrime << endl;

    // Return 0 to indicate successful execution.
    return 0;
}