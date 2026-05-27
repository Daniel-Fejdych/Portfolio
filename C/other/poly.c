#include <stdio.h>

int main(int argc, char *argv[])
{
    int a, b, c, x;
    printf("a: ");
    scanf("%d", &a);
    printf("b: ");
    scanf("%d", &b);
    printf("c: ");
    scanf("%d", &c);
    printf("x: ");
    scanf("%d", &x);
    printf("%d\n", a * x * x + b * x + c);
    return 0;
}
