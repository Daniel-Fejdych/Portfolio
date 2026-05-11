def hello(age):
    iAge = int(age)
    if iAge > 18:
        print(age + " is above 18.")
    else:
        print(age + " is not above 18.")
    
def factorial(n):
    if n == 0:
        return 1;
    else:
        return n * factorial(n-1);

def fact(n):
    ans = 1;
    for i in range(1, n):
        ans *= i;
    return ans;

hello(input("Enter your age:\n>>>"));
for i in range(10000, 10001):
    print(fact(i));

def pytrip(n):
	return [(a, b, c)
                for a in range(1, n)
                for b in range(a, n)
                for c in range(b, n) if a * a + b * b == c * c]

def concatMap(f, xs):
    return [e for x in xs for e in f(x)]

def pytripCM(n):
    concatMap(lambda a:
              [(a, b, c) for b in range(a, n) for c in range(b, n) if a * a + b * b == c * c], range(1, n))
