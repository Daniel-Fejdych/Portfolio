#include <stdio.h>

int main(int argc, char *argv[])
{
    int low, high, guess, response, count;

    low = 1;
    high = 100;
    count = 0;

    while (1) {
        guess = (high + low) / 2;
        count = count + 1;
        printf("I guess %d.\n", guess);
        printf("Am I correct (0), high (1) or low (2)? ");
        scanf("%d", &response);
        if (response == 0)
            break;
        switch (response) {
        case 1:
            high = guess;
            break;
        case 2:
            low = guess;
            break;
        default:
            printf("I don't understand %d.\n", response);
            count = count - 1;
        }
    }
    printf("I took %d guesses.\n", count);

    return 0;
}
