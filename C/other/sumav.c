#include <stdio.h>

int main(int argc, char *argv[])
{
    int count;
    int sum;
    int n;

    count = 0;
    sum = 0;
    printf("next> ");
    scanf("%d", &n);
    while (n != 0) {
        count = count + 1;
        sum = sum + n;
        printf("next> ");
        scanf("%d", &n);
    }
    printf("count: %d, sum: %d, average: %d\n", count, sum, sum / count);

    return 0;
}
