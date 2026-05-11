def factorial(a):
    b=1
    for i in range(0,a):
        b *= a - i
    return b
