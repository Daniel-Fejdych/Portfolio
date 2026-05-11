def factorial(a):
    b=1
    for i in range(0,a):
        b *= a - i
    return b
for i in range(0, 100):
    print(factorial(int(input("The No. to Factorialise\n:"))))
