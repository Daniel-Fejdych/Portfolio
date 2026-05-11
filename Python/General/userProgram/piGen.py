import sys
from decimal import Decimal, getcontext

def compute_pi_digits(n: int):
    """Return the first n digits of π as a list of integers."""
    if n <= 0:
        return []

    # Use extra guard digits to ensure correct rounding
    precision = n + 20
    getcontext().prec = precision

    # Chudnovsky constants
    A = Decimal(13591409)
    B = Decimal(545140134)
    C3 = Decimal(262537412640768000)      # 640320**3
    sqrt10005 = Decimal(10005).sqrt()
    const = Decimal(426880) * sqrt10005   # 426880 * sqrt(10005)

    # First term of the series (k = 0)
    term = A
    total = term
    k = 0

    # Sum the series until the next term becomes negligible
    threshold = Decimal(10) ** (-precision)
    while True:
        # Compute term_{k+1} from term_k using recurrence
        sixk = 6 * k
        num_prod = (sixk + 1) * (sixk + 2) * (sixk + 3) * (sixk + 4) * (sixk + 5) * (sixk + 6)
        num_factor = A + B * (k + 1)
        numerator = num_prod * num_factor

        threek = 3 * k
        den_prod = (threek + 1) * (threek + 2) * (threek + 3)
        den_factor = (k + 1) ** 3 * C3 * (A + B * k)
        denominator = den_prod * den_factor

        ratio = -Decimal(numerator) / Decimal(denominator)
        next_term = term * ratio

        if abs(next_term) < threshold:
            break

        total += next_term
        term = next_term
        k += 1

    # Compute π
    pi = const / total

    # Extract the digits as a list of integers
    pi_str = format(pi, 'f')          # fixed-point string, e.g. "3.14159..."
    int_part, frac_part = pi_str.split('.')
    digits = [int(ch) for ch in int_part]          # always ['3']
    if n > 1:
        frac_digits = [int(ch) for ch in frac_part[:n-1]]
        digits.extend(frac_digits)

    return digits[:n]                 # ensure exactly n digits

if __name__ == "__main__":
    # Read n from console
    n = int(sys.stdin.readline().strip())
    result = compute_pi_digits(n)
    print(result)
