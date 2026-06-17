/*
    Quadratic Equation Root Calculator
    ----------------------------------

    This program calculates the roots (solutions) of a quadratic equation
    in the form:

        y = ax^2 + bx + c

    To find the roots, we set y = 0:

        ax^2 + bx + c = 0

    We then use the quadratic formula:

                 -b ± √(b² - 4ac)
        x = ----------------------
                       2a

    The value inside the square root is called the discriminant:

        discriminant = b² - 4ac

    The discriminant determines the number of roots:

    - If discriminant > 0
      There are two different real roots.

    - If discriminant == 0
      There is one repeated real root.

    - If discriminant < 0
      There are two complex (imaginary) roots.

*/

#include <iostream> // Allows input and output
#include <cmath>    // Provides sqrt() function

using namespace std;

int main()
{
    // Create variables to store the coefficients.
    // double is used because coefficients may contain decimals.
    double a, b, c;

    // Ask the user to enter coefficient a.
    cout << "Enter value for a: ";
    cin >> a;

    // Ask the user to enter coefficient b.
    cout << "Enter value for b: ";
    cin >> b;

    // Ask the user to enter coefficient c.
    cout << "Enter value for c: ";
    cin >> c;

    // A quadratic equation requires a ≠ 0.
    // If a is 0, the equation is no longer quadratic.
    if (a == 0)
    {
        cout << "\nError: 'a' cannot be 0 because the equation would not be quadratic." << endl;

        // End the program immediately.
        return 1;
    }

    // Calculate the discriminant.
    double discriminant = (b * b) - (4 * a * c);

    // Case 1: Two different real roots
    if (discriminant > 0)
    {
        // Calculate both roots.
        double root1 = (-b + sqrt(discriminant)) / (2 * a);
        double root2 = (-b - sqrt(discriminant)) / (2 * a);

        cout << "\nThe equation has two real roots." << endl;
        cout << "Root 1 = " << root1 << endl;
        cout << "Root 2 = " << root2 << endl;
    }

    // Case 2: One repeated real root
    else if (discriminant == 0)
    {
        // Only one root exists.
        double root = -b / (2 * a);

        cout << "\nThe equation has one repeated real root." << endl;
        cout << "Root = " << root << endl;
    }

    // Case 3: Two complex roots
    else
    {
        /*
            For negative discriminants:

            sqrt(negative number) is not a real number.

            We separate the real and imaginary parts.

            Example:

            (-b ± √(-16)) / (2a)

            becomes

            real part ± imaginary part i
        */

        double realPart = -b / (2 * a);

        double imaginaryPart = sqrt(-discriminant) / (2 * a);

        cout << "\nThe equation has two complex roots." << endl;

        cout << "Root 1 = "
             << realPart
             << " + "
             << imaginaryPart
             << "i"
             << endl;

        cout << "Root 2 = "
             << realPart
             << " - "
             << imaginaryPart
             << "i"
             << endl;
    }

    // Indicate successful completion.
    return 0;
}